# TheMovieDB
# Multi-language and multi-country support added by Aqntbghd

# TODO : Deal with TMDB set of films as collections as soon as the API is made public
# TODO : Add more countries (prefs and automatic) and test test test it


import time

TMDB_GETINFO_IMDB = 'http://api.themoviedb.org/2.1/Movie.imdbLookup/en/json/a3dc111e66105f6387e99393813ae4d5/%s'
TMDB_GETINFO_TMDB = 'http://api.themoviedb.org/2.1/Movie.getInfo/%s/json/a3dc111e66105f6387e99393813ae4d5/%s'
TMDB_GETINFO_HASH = 'http://api.themoviedb.org/2.1/Hash.getInfo/%s/json/a3dc111e66105f6387e99393813ae4d5/%s'

TMDB_LANGUAGE_CODES = {
  'cs': 'cs',
  'da': 'da',
  'de': 'de',
  'en': 'en',
  'es': 'es',
  'fr': 'fr',
  'it': 'it',
  'nl': 'nl',
  'pt': 'pt',
  'sv': 'sv',
  'zh': 'zh'
}

# See defaultPrefs.json for the default values here.
TMDB_COUNTRY_CODES = {
  'Automatic': '',
  'Argentina': '-AR',
  'Australia': '-AU',
  'Austria': '-AT',
  'Belgium': '-BE',
  'Belize': '-BZ',
  'Bolivia': '-BO',
  'Brazil': '-BR',
  'Canada': '-CA',
  'Chile': '-CL',
  'Colombia': '-CO',
  'Costa Rica': '-CR',
  'Czech Republic': '-CZ',
  'Dominican Republic': '-DO',
  'Ecuador': '-EC',
  'El Salvador': '-SV',
  'France': '-FR',
  'Germany': '-DE',
  'Guatemala': '-GT',
  'Honduras': '-HN',
  'Hong Kong SAR': '-HK',
  'Ireland': '-IE',
  'Italy': '-IT',
  'Jamaica': '-JM',
  'Liechtenstein': '-LI',
  'Luxembourg': '-LU',
  'Mexico': '-MX',
  'Netherlands': '-NL',
  'New Zealand': '-NZ',
  'Nicaragua': '-NI',
  'Panama': '-PA',
  'Paraguay': '-PY',
  'Peru': '-PE',
  'Portugal': '-PT',
  'Peoples Republic of China': '-CN',
  'Puerto Rico': '-PR',
  'Singapore': '-SG',
  'South Africa': '-ZA',
  'Spain': '-ES',
  'Switzerland': '-CH',
  'Taiwan': '-TW',
  'Trinidad': '-TT',
  'United Kingdom': '-GB',
  'United States': '-US',
  'Uruguay': '-UY',
  'Venezuela': '-VE'
}
# See defaultPrefs.json for the default values here.
TMDB_LANG_TO_COUNTRY = {
  'cs': '-CZ',
  'de': '-DE',
  'en': '-US',
  'es': '-ES',
  'fr': '-FR',
  'it': '-IT',
  'nl': '-NL',
  'pt': '-PT',
  'zh': '-CN'
}

def Start():
  HTTP.CacheTime = CACHE_1HOUR * 4
  Log('Starting TheMovieDB agent.')

def GetLanguageCode(lang):
  if TMDB_LANGUAGE_CODES.has_key(lang):
    return TMDB_LANGUAGE_CODES[lang]
  else:
    return 'en'

def GetCountryCode(country):
  if TMDB_COUNTRY_CODES.has_key(country):
    return TMDB_COUNTRY_CODES[country]
  else:
    return ''

def GetCountryCodeByLang(lang):
  if TMDB_LANG_TO_COUNTRY.has_key(lang):
    return TMDB_LANG_TO_COUNTRY[lang]
  else:
    return ''

def GetTMDBLangAndCountryCode(lang):
  output = GetLanguageCode(lang)
  if Prefs['country'] == "Automatic" :
    output += GetCountryCodeByLang(lang) 
  else:
    output += GetCountryCode(Prefs['country'])
  return output

@expose
def GetImdbIdFromHash(openSubtitlesHash, lang):
  try:
    tmdb_dict = JSON.ObjectFromURL(TMDB_GETINFO_HASH % (GetLanguageCode(lang), str(openSubtitlesHash)))[0]
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
  name = 'TheMovieDB'
  languages = [Locale.Language.English, Locale.Language.Swedish, Locale.Language.French,
               Locale.Language.Spanish, Locale.Language.Dutch, Locale.Language.German,
               Locale.Language.Italian, Locale.Language.Danish]
  primary_provider = False
  contributes_to = ['com.plexapp.agents.imdb']

  def search(self, results, media, lang):
    Log("Entering search (%s,%s)" % (media.primary_metadata.id,lang))
    if media.primary_metadata is not None:
      tmdb_id = self.get_tmdb_id(media.primary_metadata.id) # get the TMDb ID using the IMDB ID
      if tmdb_id:
        results.Append(MetadataSearchResult(id = tmdb_id, score = 100))
    elif media.openSubtitlesHash is not None:
      match = GetImdbIdFromHash(media.openSubtitlesHash, lang)

  def update(self, metadata, media, lang): 
    proxy = Proxy.Preview
    Log('Update called : Lang=%s\tComputed Country=%s\tMetadata.id=%s' % (lang, GetTMDBLangAndCountryCode(lang), metadata.id))
    try:
      tmdb_info = HTTP.Request(TMDB_GETINFO_TMDB % (GetTMDBLangAndCountryCode(lang), metadata.id)).content
      if tmdb_info.count('503 Service Unavailable') > 0:
        time.sleep(5)
        tmdb_info = HTTP.Request(TMDB_GETINFO_TMDB % (GetTMDBLangAndCountryCode(lang), metadata.id), cacheTime=0).content
      tmdb_dict = JSON.ObjectFromString(tmdb_info)[0] #get the full TMDB info record using the TMDB id
    except:
      Log('Exception fetching JSON from theMovieDB (1).')
      return None

    # Rating.
    if tmdb_dict['votes'] is not None and tmdb_dict['rating'] is not None:
      votes = tmdb_dict['votes']
      rating = tmdb_dict['rating']
      if votes > 3:
        metadata.rating = rating

    # Title of the film.
    if Prefs['title']:
      if tmdb_dict['name'] is not None:
        metadata.title = tmdb_dict['name']
    else:
      metadata.title = ""

    # Tagline.
    if tmdb_dict['tagline'] is not None:
      metadata.tagline = tmdb_dict['tagline']

    # Content rating.
    if tmdb_dict['certification'] is not None:
      if GetTMDBLangAndCountryCode(lang) == 'fr-FR':
         # we have a special case for french people, we may have to support it also for nl (see Media-Flags.bundle)
         # TODO: ask plex devs to i18n the mediaflags ratings
         metadata.content_rating = "fr/" + tmdb_dict['certification']
      else :
         metadata.content_rating = tmdb_dict['certification']

    # Summary.
    if tmdb_dict['overview'] is not None:
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
# Aqntbghd: Commented, used for debug in case of douts about the matching.
#    for m in JSON.ObjectFromString(tmdb_info):
#      Log("Looking for %s I found %s as %s" %(str(imdb_id),str(m['id']),str(m['imdb_id'])))
    if tmdb_dict and isinstance(tmdb_dict, dict):
      return str(tmdb_dict['id'])
    else:
      return None
