#themoviedb
#note: right now, themoviedb only supports "en" for language
#note : This is a first try to get it supporting other languages, first try : let's change it to francais. (made done by Aqntbghd)

# TODO : default to english if the localized version is not found ? but why ? isn't it a way to place english as superior to all other languages ? :)
# TODO : Deal with languages AND locations as TMDB makes the difference between them.
# TODO : Deal with TMDB set of films as collections as soon as the API is made public

import time

#that one does not need to be localized (why ? i don't know but i think it might break it).
TMDB_GETINFO_IMDB = 'http://api.themoviedb.org/2.1/Movie.imdbLookup/en/json/a3dc111e66105f6387e99393813ae4d5/%s'

# These two are localized to use a language and country code as a parameter (for example 'fr-FR' for french in FRance)
# so we have to map the language to that code unles Plex supports localization and internationalisation (l10n and i18n)

TMDB_GETINFO_TMDB = 'http://api.themoviedb.org/2.1/Movie.getInfo/%s/json/a3dc111e66105f6387e99393813ae4d5/%s'
TMDB_GETINFO_HASH = 'http://api.themoviedb.org/2.1/Hash.getInfo/%s/json/a3dc111e66105f6387e99393813ae4d5/%s'


def Start():
  HTTP.CacheTime = CACHE_1HOUR * 4
  
@expose
def GetImdbIdFromHash(openSubtitlesHash, lang):
  try:
  # Language table
    THEMOVIEDB_LANGUAGES_CODES = {
      'fr': 'fr-FR',
      'en': 'en',
      'nl': 'nl',
      'de': 'de',
      'it': 'it',
      'es': 'es',
      'da': 'da'
    }
    tmdb_dict = JSON.ObjectFromURL(TMDB_GETINFO_HASH % (THEMOVIEDB_LANGUAGES_CODES[lang],str(openSubtitlesHash)))[0]
    if isinstance(tmdb_dict, dict) and tmdb_dict.has_key('imdb_id'):
      return MetadataSearchResult(
        id    = tmdb_dict['imdb_id'],
        name  = tmdb_dict['name'],
        year  = None,
        lang  = lang,
        score = 94)
    else:
      return None
    
  except:
    return None
  
class TMDbAgent(Agent.Movies):

  name = 'TheMovieDB-Aqntbghd'
  # languages = [Locale.Language.English, 'fr']
  languages = [Locale.Language.English, 'fr', 'nl', 'de', 'it', 'es','da']

  primary_provider = False
  contributes_to = ['com.plexapp.agents.imdb']
  
  def search(self, results, media, lang):
    if media.primary_metadata is not None:
      tmdb_id = self.get_tmdb_id(media.primary_metadata.id) # get the TMDb ID using the IMDB ID
      if tmdb_id:
        results.Append(MetadataSearchResult(id = tmdb_id, score = 100))
    elif media.openSubtitlesHash is not None:
      match = GetImdbIdFromHash(media.openSubtitlesHash, lang)

  def update(self, metadata, media, lang): 
  # Language table
    THEMOVIEDB_LANGUAGES_CODES = {
      'fr': 'fr-FR',
      'en': 'en',
      'nl': 'nl',
      'de': 'de',
      'it': 'it',
      'es': 'es',
      'da': 'da'
    }
    proxy = Proxy.Preview
    try:
      tmdb_info = HTTP.Request(TMDB_GETINFO_TMDB % (THEMOVIEDB_LANGUAGES_CODES[lang],metadata.id)).content
      if tmdb_info.count('503 Service Unavailable') > 0:
        time.sleep(5)
        tmdb_info = HTTP.Request(TMDB_GETINFO_TMDB % (THEMOVIEDB_LANGUAGES_CODES[lang],metadata.id), cacheTime=0).content
      tmdb_dict = JSON.ObjectFromString(tmdb_info)[0] #get the full TMDB info record using the TMDB id
    except:
      Log('Exception fetching JSON from theMovieDB (1).')
      return None

    # Rating.
    votes = tmdb_dict['votes']
    rating = tmdb_dict['rating']
    if votes > 3:
      metadata.rating = rating
    
    # Title of the film.
    metadata.title = tmdb_dict['name']

    # Tagline.
    metadata.tagline = tmdb_dict['tagline']
      
    # Content rating.
    metadata.content_rating = tmdb_dict['certification']
      
    # Summary.
    metadata.summary = tmdb_dict['overview']
    if metadata.summary == 'No overview found.':
      metadata.summary = ""
    
    # Release date.
    try: 
      metadata.originally_available_at = Datetime.ParseDate(tmdb_dict['released']).date()
      metadata.year = metadata.originally_available_at.year
    except: 
      pass
      
    # Runtime.
    try: metadata.duration = int(tmdb_dict['runtime']) * 60 * 1000
    except: pass
      
    # Genres.
    metadata.genres.clear()
    for genre in tmdb_dict['genres']:
      metadata.genres.add(genre['name'])
      
    # Studio.
    try: metadata.studio = tmdb_dict['studios'][0]['name']
    except: pass

    # Cast.
    metadata.directors.clear()
    metadata.writers.clear()
    metadata.roles.clear()
    
    for member in tmdb_dict['cast']:
      if member['job'] == 'Director':
        metadata.directors.add(member['name'])
      elif member['job'] == 'Author':
        metadata.writers.add(member['name'])
      elif member['job'] == 'Actor':
        role = metadata.roles.new()
        role.role = member['character']
        role.actor = member['name']
    
    i = 0
    valid_names = list()
    for p in tmdb_dict['posters']:
      if p['image']['size'] == 'original':
        i += 1
        valid_names.append(p['image']['url'])
        if p['image']['url'] not in metadata.posters:
          p_id = p['image']['id']
          
          # Find a thumbnail.
          for t in tmdb_dict['posters']:
            if t['image']['id'] == p_id and t['image']['size'] == 'mid':
              thumb = HTTP.Request(t['image']['url'])
              break
              
          try: metadata.posters[p['image']['url']] = proxy(thumb, sort_order = i)
          except: pass
    
    metadata.posters.validate_keys(valid_names)
    valid_names = list()
    
    i = 0
    for b in tmdb_dict['backdrops']:
      if b['image']['size'] == 'original':
        i += 1
        valid_names.append(b['image']['url'])
        if b['image']['url'] not in metadata.art:
          b_id = b['image']['id']
          for t in tmdb_dict['backdrops']:
            if t['image']['id'] == b_id and t['image']['size'] == 'poster':
              thumb = HTTP.Request(t['image']['url'])
              break 
          try: metadata.art[b['image']['url']] = proxy(thumb, sort_order = i)
          except: pass
            
    metadata.art.validate_keys(valid_names)
    
  def get_tmdb_id(self, imdb_id):
    try:
      tmdb_info = HTTP.Request(TMDB_GETINFO_IMDB % str(imdb_id)).content
      if tmdb_info.count('503 Service Unavailable') > 0:
        time.sleep(5)
        tmdb_info = HTTP.Request(TMDB_GETINFO_IMDB % str(imdb_id), cacheTime=0).content
      tmdb_dict = JSON.ObjectFromString(tmdb_info)[0]
    except:
      Log('Exception fetching JSON from theMovieDB (2).')
      return None
    if tmdb_dict and isinstance(tmdb_dict, dict):
      return str(tmdb_dict['id'])
    else:
      return None
