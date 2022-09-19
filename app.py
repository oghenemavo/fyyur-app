#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import pickle
import pprint
import re
import dateutil.parser
import babel
# from flask import Flask, jsonify, render_template, request, Response, flash, redirect, url_for
from flask import (
  Flask, 
  jsonify,
  render_template, 
  request, 
  Response, 
  flash, 
  redirect, 
  url_for
)
from flask_moment import Moment
from models import db, Venue, Artist, Show 
# from flask_sqlalchemy import SQLAlchemy, get_debug_queries
from sqlalchemy.orm import load_only
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from sqlalchemy import column, select
from forms import *
from sqlalchemy import func
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
# db = SQLAlchemy(app)
db.init_app(app)
migrate = Migrate(app, db)

# TODO: connect to a local postgresql database

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  # TODO: replace with real venues data.
  #       num_upcoming_shows should be aggregated based on number of upcoming shows per venue.
  venuesObject = db.session.query(Venue).with_entities(Venue.city, Venue.state, Venue.name, Venue.id, func.count(Venue.id)).group_by(Venue.city, Venue.state, Venue.name, Venue.id)
  
  results = {}
  for city, state, name, id, show_count in venuesObject:
    location = (city, state)
    if location not in results:
      results[location] = []
    results[location].append({"id": id, "name": name, "num_upcoming_shows": show_count})

  data = [];
  for key, value in results.items():
    locationVenues = {
      'city': key[0],
      'state': key[1],
      'venues': value,
    }
    data.append(locationVenues)

  # venues = Venue.query.group_by(Venue.city, Venue.state).all()
  # venues = db.session.query(Venue).group_by(Venue.city, Venue.state, Venue.id).all()
  # print(dir(venues[0]))
  # json.dumps(areaList)

  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for Hop should return "The Musical Hop".
  # search for "Music" should return "The Musical Hop" and "Park Square Live Music & Coffee"

  search = request.form['search_term']

  venueSearchObject = db.session.query(Venue).with_entities(
    Venue.id, Venue.name, func.count(Venue.id), func.count(Show.id)
  ).filter(Artist.name.like('%' + search + '%')).join(
    Show, Show.venue_id == Venue.id
  ).group_by(Venue.id).all()

  response = {}
  response['data'] = []
  for id, name, artist_count, show_count in venueSearchObject:
    response['count'] = artist_count
    response['data'].append({"id": id, "name": name, "num_upcoming_shows": show_count})
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  # shows the venue page with the given venue_id
  # TODO: replace with real venue data from the venues table, using venue_id
  
  venue = db.session.query(Venue).filter_by(id=venue_id).first()
  past_shows = db.session.query(Show).with_entities( 
    Artist.id.label("artist_id"), Artist.name.label("artist_name"), Artist.image_link.label("artist_image_link"),
    Show.start_time, func.count(Show.id).label("show_count")
  ).join(
    Artist, Artist.id == Show.artist_id
  ).filter(Show.venue_id == venue_id).group_by(Artist.id, Show.start_time).all()
  upcoming_shows = db.session.query(Show).with_entities( 
    Artist.id.label("artist_id"), Artist.name.label("artist_name"), Artist.image_link.label("artist_image_link"),
    Show.start_time, func.count(Show.id).label("show_count")
  ).join(
    Artist, Artist.id == Show.artist_id
  ).filter(Show.venue_id == venue_id).group_by(Artist.id, Show.start_time).all()

  results = {}
  results["past_shows_count"] = 0
  results["upcoming_shows_count"] = 0
  results["past_shows"] = results["upcoming_shows"] = []

  for attr, value in venue.__dict__.items():
    if (attr == 'genres'):
      results[attr] = json.loads(value)
    else:
      results[attr] = value

  for x in past_shows:
    if x:
      results["past_shows"].append({"artist_id": x.artist_id, "artist_name": x.artist_name, "artist_image_link": x.artist_image_link, "start_time": x.start_time})
      results["past_shows_count"] += 1

  for x in upcoming_shows:
    if x:
      results["upcoming_shows"].append({"artist_id": x.artist_id, "artist_name": x.artist_name, "artist_image_link": x.artist_image_link, "start_time": x.start_time})
      results["upcoming_shows_count"] += 1
  
  return render_template('pages/show_venue.html', venue=results)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm(request.form, meta={'csrf': False})

  if form.validate():
    try:
      venue = Venue(
        name=form.name.data,
        city=form.city.data,
        state=form.state.data,
        address=form.address.data,
        phone=form.phone.data,
        image_link=form.image_link.data,
        facebook_link=form.facebook_link.data,
        genres=form.genres.data,
        website=form.website_link.data,
        seeking_talent= True if form.seeking_talent == 'y' else False,
        seeking_description=form.seeking_description.data
      )
      db.session.add(venue)
      db.session.commit()
      flash('Venue: {0} created successfully'.format(venue.name))
    except ValueError as err:
      print(err)

      flash('An error occurred creating the Venue: {0}. Error: {1}'.format(venue.name, err))
      db.session.rollback()
    finally:
      db.session.close()
  else:
    message = []
    for field, err in form.errors.items():
      message.append(field + ' ' + '|'.join(err))
    flash('Errors ' + str(message))

  return render_template('pages/home.html')
  

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  # TODO: Complete this endpoint for taking a venue_id, and using
  # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.
  Venue.query.filter_by(id=venue_id).delete()

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return jsonify({
    'status': True,
    'message': 'Todo Deleted Successfully',
  })

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  # TODO: replace with real data returned from querying the database
  data = db.session.query(Artist.id, Artist.name).all()
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  # TODO: implement search on artists with partial string search. Ensure it is case-insensitive.
  # seach for "A" should return "Guns N Petals", "Matt Quevado", and "The Wild Sax Band".
  # search for "band" should return "The Wild Sax Band".
  search = request.form['search_term']

  artistSearchObject = db.session.query(Artist).with_entities(
    Artist.id, Artist.name, func.count(Artist.id), func.count(Show.id)
  ).filter(Artist.name.like('%' + search + '%')).join(
    Show, Show.artist_id == Artist.id
  ).group_by(Artist.id).all()

  print(artistSearchObject)

  response = {}
  response['data'] = []
  for id, name, artist_count, show_count in artistSearchObject:
    response['count'] = artist_count
    response['data'].append({"id": id, "name": name, "num_upcoming_shows": show_count})

  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = db.session.query(Artist).filter_by(id=artist_id).first()
  past_shows = db.session.query(Show).with_entities( 
    Venue.id.label("venue_id"), Venue.name.label("venue_name"), Venue.image_link.label("venue_image_link"),
    Show.start_time, func.count(Show.id).label("show_count")
  ).join(
    Venue, Venue.id == Show.venue_id
  ).filter(Show.venue_id == artist_id).group_by(Venue.id, Show.start_time).all()
  upcoming_shows = db.session.query(Show).with_entities( 
    Venue.id.label("venue_id"), Venue.name.label("venue_name"), Venue.image_link.label("venue_image_link"),
    Show.start_time, func.count(Show.id).label("show_count")
  ).join(
    Venue, Venue.id == Show.venue_id
  ).filter(Show.artist_id == artist_id).group_by(Venue.id, Show.start_time).all()

  results = {}
  results["past_shows_count"] = 0
  results["upcoming_shows_count"] = 0
  results["past_shows"] = results["upcoming_shows"] = []

  for attr, value in artist.__dict__.items():
    if (attr == 'genres'):
      results[attr] = json.loads(value)
    else:
      results[attr] = value

  for x in past_shows:
    if x:
      results["past_shows"].append({"venue_id": x.venue_id, "venue_name": x.venue_name, "venue_image_link": x.venue_image_link, "start_time": x.start_time})
      results["past_shows_count"] += 1

  for x in upcoming_shows:
    if x:
      results["upcoming_shows"].append({"venue_id": x.venue_id, "venue_name": x.venue_name, "venue_image_link": x.venue_image_link, "start_time": x.start_time})
      results["upcoming_shows_count"] += 1

  return render_template('pages/show_artist.html', artist=results)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get(artist_id)
  
  form = ArtistForm()
  # TODO: populate form with fields from artist with ID <artist_id>
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm(request.form)

  if form.validate():
    try:
      artist = Artist.query.get(artist_id)

      artist.name=form.name.data
      artist.city=form.city.data
      artist.state=form.state.data
      artist.phone=form.phone.data
      artist.genres=form.genres.data
      artist.image_link=form.image_link.data
      artist.facebook_link=form.facebook_link.data
      artist.website=form.website_link.data
      artist.seeking_venue=True if form.seeking_venue == 'y' else False
      artist.seeking_description=form.seeking_description.data

      db.session.commit()
      flash('Artist: {0} Edited successfully'.format(artist.name))
    except Exception as err:
      flash('An error occurred Editing the Artist: {0}. Error: {1}'.format(artist.name, err))
      db.session.rollback()
    finally:
      db.session.close()
  else:
    message = []
    for field, err in form.errors.items():
      message.append(field + ' ' + '|'.join(err))
    flash('Errors ' + str(message))   

  return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Artist.query.get(venue_id)
  form = VenueForm()
  # TODO: populate form with values from venue with ID <venue_id>
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm(request.form)

  if form.validate():
    try:
      venue = Venue.query.get(venue_id)
      venue.name=form.name.data
      venue.city=form.city.data
      venue.state=form.state.data
      venue.address=form.address.data
      venue.phone=form.phone.data
      venue.image_link=form.image_link.data
      venue.facebook_link=form.facebook_link.data
      venue.genres=form.genres.data
      venue.website=form.website_link.data
      venue.seeking_talent= True if form.seeking_talent == 'y' else False
      venue.seeking_description=form.seeking_description.data

      db.session.commit()
      flash('Venue: {0} Edited successfully'.format(venue.name))
    except Exception as err:
      flash('An error occurred editing the Venue: {0}. Error: {1}'.format(venue.name, err))
      db.session.rollback()
    finally:
      db.session.close()
  else:
    message = []
    for field, err in form.errors.items():
      message.append(field + ' ' + '|'.join(err))
    flash('Errors ' + str(message))   

  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  form = ArtistForm(request.form)

  if form.validate():
    try:
      artist = Artist(
        name=form.name.data,
        city=form.city.data,
        state=form.state.data,
        phone=form.phone.data,
        image_link=form.image_link.data,
        facebook_link=form.facebook_link.data,
        genres=form.genres.data,
        website=form.website_link.data,
        seeking_venue= True if form.seeking_venue == 'y' else False,
        seeking_description=form.seeking_description.data
      )
      db.session.add(artist)
      db.session.commit()
      flash('Artist: {0} created successfully'.format(artist.name))
    except Exception as err:
      flash('An error occurred creating the Artist: {0}. Error: {1}'.format(artist.name, err))
      db.session.rollback()
    finally:
      db.session.close()
  else:
    message = []
    for field, err in form.errors.items():
      message.append(field + ' ' + '|'.join(err))
    flash('Errors ' + str(message))

  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  result = db.session.query(Show).with_entities(Show.venue_id, Show.artist_id, Show.start_time, 
    Venue.name.label("venue_name"), 
    Artist.name.label("artist_name"), Artist.image_link.label("artist_image_link")
  ).join(Venue, Venue.id == Show.venue_id).join(Artist, Artist.id == Show.artist_id).all()

  # for record in result:
    # pprint.pprint(record.__dict__)

  show_list = [dict(row) for row in result]

  # displays list of shows at /shows
  # TODO: replace with real venues data.
  return render_template('pages/shows.html', shows=show_list)

@app.route('/shows/create')
def create_shows():
  artist_list = db.session.query(Artist).with_entities(Artist.id, Artist.name).all()
  venue_list = db.session.query(Venue).with_entities(Venue.id, Venue.name).all()
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form, artists=artist_list, venues=venue_list)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  form = ShowForm(request.form)

  if form.validate():
    try:
      show = Show(
        venue_id=form.venue_id.data,
        artist_id=form.artist_id.data,
        start_time=form.start_time.data,
      )
      db.session.add(show)
      db.session.commit()
      flash('Show was successfully listed!')
    except Exception as err:
      flash('An error occurred creating the Show: {0}. Error: {1}'.format(show.venue_id, err))
      db.session.rollback()
    finally:
      db.session.close()
  else:
    message = []
    for field, err in form.errors.items():
      message.append(field + ' ' + '|'.join(err))
    flash('Errors ' + str(message))

  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
