import pandas as pd
import gtfstk as gt


SCHOOL_STRINGS = [
  'college', 
  'intermediate', 
  'grammar', 
  'primary',
  'high', 
  'school',
  'sch',
  'boys',
  'girls',
  'Rosmini',
  'St Marks',
  'Clendon to Manurewa and Greenmeadows',
  'Sacred Heart'
  ]

def drop_school_routes(feed, max_trips=4, school_strings=SCHOOL_STRINGS):
    """
    Given a GTFSTK Feed object, drop routes that appear to be school 
    routes, along with their associated trips and stop times, 
    and return the resulting new feed.

    School route criteria, all of which must be satisfied:

    - route is a bus
    - route has at most ``max_trips`` trips
    - route long name contains one of the strings in ``school_strings``
    """
    r = feed.routes

    # Route is a bus
    cond_bus = r['route_type'] == 3
        
    # Route has at most max_trips
    t = feed.trips.groupby('route_id').count().reset_index()
    rids = t[t['trip_id'] <= max_trips]['route_id'].copy()
    cond_max_trips = r['route_id'].isin(rids)

    # Route long name contains school-like word
    cond_schoolish_name = False
    for s in school_strings:
        cond_schoolish_name |= r['route_long_name'].str.contains(s, case=False)
    
    # Conjoin criteria
    cond = cond_bus & cond_max_trips & cond_schoolish_name

    # Take complement to get non-school routes
    feed.routes = r[~cond].copy()

    # Get non-school trips
    rids = feed.routes['route_id']
    feed.trips = feed.trips[feed.trips['route_id'].isin(rids)].copy()

    # Remove school stop times
    st = feed.stop_times
    feed.stop_times = st[st['trip_id'].isin(feed.trips['trip_id'])].copy()

    return feed 

def clean(feed):
    """
    Given a GTFSTK object representing an Auckland GTFS feed, drop the school routes, aggregate the routes by route_short_name, clean the stop codes by adding leading zeros where necessary, and return the resulting feed.
    """
    feed = drop_school_routes(feed)
    feed = gt.aggregate_routes(feed)

    # Add leading zeros to stop codes
    def clean_stop_code(x):
        n = len(x)
        if n < 4 :
            x = '0'*(4 - n) + x
        return x
    
    s = feed.stops 
    s['stop_code'] = s['stop_code'].map(clean_stop_code)
    feed.stops = s

    return feed
