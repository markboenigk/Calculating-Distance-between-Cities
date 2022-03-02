import pandas as pd
import numpy as np
from sklearn.metrics import DistanceMetric
from geopy.geocoders import Nominatim
import time
from pprint import pprint
import haversine as hs
import math
import plotly.express as px

app = Nominatim(user_agent="test")

#locations = ['Boston', 'Frankfurt', 'Hamburg']
locations = [
    str(n) for n in input("Enter cities (seperation with , ): ").split(',')
]


def get_location_by_address(address):
    """This function returns a location as raw from an address
    will repeat until success. Function sleeps for one second to avoid error"""
    time.sleep(1)
    try:
        return app.geocode(address).raw
    except:
        return get_location_by_address(address)


def get_locations_df(locations):
    """This function returns a pandas dataframe with all location names, Latitude, Longitude and the radians for the Latitude and Longitude """
    location_list = []
    for i in locations:
        loc = get_location_by_address(i)
        location = [i, float(loc['lat']), float(loc['lon'])]
        location_list.append(location)
    location_df = pd.DataFrame(data=location_list,
                               columns=['City', 'Latitude', 'Longitude'])
    # add columns with radians for latitude and longitude
    location_df[['lat_radians', 'long_radians'
                 ]] = (np.radians(location_df.loc[:,
                                                  ['Latitude', 'Longitude']]))
    return location_df


location_df = get_locations_df(locations)


def get_df_locations(location_df):
    """This function calculates the distance between the cities and returns a dataframe """
    df = pd.DataFrame(columns=["From", "To", "Kilometers"])
    for i in location_df.index[:-1]:
        loc = location_df[i:].reset_index(drop=True)
        loc_a = loc.iloc[:1]
        loc_a = loc_a.rename(columns={loc_a.columns[0]: 'From'})
        loc_b = location_df[i + 1:].reset_index(drop=True)
        loc_b = loc_b.rename(columns={loc_b.columns[0]: 'To'})
        #dist = sklearn.metrics.DistanceMetric.get_metric('haversine')
        dist = DistanceMetric.get_metric('haversine')
        dist_matrix = (dist.pairwise(loc_a[['lat_radians', 'long_radians']],
                                     loc_b[['lat_radians', 'long_radians']]) *
                       3959)
        df_dist_matrix = (pd.DataFrame(dist_matrix,
                                       index=loc_a['From'],
                                       columns=loc_b['To']))
        df_dist_long = (pd.melt(df_dist_matrix.reset_index(), id_vars='From'))
        df_dist_long = df_dist_long.rename(
            columns={df_dist_long.columns[2]: 'Kilometers'})
        df = df.append(df_dist_long).reset_index(drop=True)
    return df


def get_all_distances():
    """This function adds all possible routes to the dataframe from the get_df_location function and returns a dataframe"""
    df = get_df_locations(location_df)
    df = df[["To", 'From', "Kilometers"]]
    df = df.rename(columns={df.columns[0]: 'From', df.columns[1]: 'To'})
    df_total = get_df_locations(location_df).append(df)
    df_total = df_total.sort_values(by=['From', 'To']).reset_index(drop=True)
    return df_total


print(get_all_distances())


def cartesian_coordinates():
    """This function calculates the cortesian coordinates from the geocoordinates from the cities and returns a x,y,z coordinate"""
    location_df = get_locations_df(locations)
    list_lat = list(location_df["lat_radians"])
    list_lon = list(location_df["long_radians"])

    cos_lat = [math.cos(i) for i in list_lat]
    sin_lat = [math.sin(i) for i in list_lat]
    cos_lon = [math.cos(i) for i in list_lon]
    sin_lon = [math.sin(i) for i in list_lon]

    x_1_list = [lat * lon for lat, lon in zip(cos_lat, cos_lon)]
    y_1_list = [lat * lon for lat, lon in zip(cos_lat, sin_lon)]
    z_1_list = sin_lat

    x = sum(x_1_list)
    y = sum(y_1_list)
    z = sum(z_1_list)
    return x, y, z


x, y, z = cartesian_coordinates()


def get_middle_point_coordinates(x, y, z):
    """Thsi function uses the x,y,z coordinates from the cortesian_coordinates function to calculate the middlepoint of the cities/ locations and returns the latitude, longitude and the address of the middle point"""
    lon = math.atan2(y, x)
    hyp = math.sqrt(x * x + y * y)
    lat = math.atan2(z, hyp)

    lat = lat * 180 / math.pi
    lon = lon * 180 / math.pi
    middlepoint = (lat, lon)
    middlepoint_address = app.reverse(middlepoint)

    return lat, lon, middlepoint_address


Latitude = get_middle_point_coordinates(x, y, z)[0]
Longitude = get_middle_point_coordinates(x, y, z)[1]
middlepoint_address = get_middle_point_coordinates(x, y, z)[2]

print("Address of middle point:")
print(middlepoint_address)
print("Geocordinates of middle point:")
print(Latitude, Longitude)


def get_locations_map(Latitude, Longitude):
    """This funtion returns a map in plotly with the cities and the middlepoint"""
    middlepoint = {
        "City": ["Middlepoint"],
        "Latitude": [Latitude],
        "Longitude": [Longitude]
    }
    df_middlepoint = pd.DataFrame(data=middlepoint)
    location_graph_df = location_df[["City", "Latitude", "Longitude"]]
    location_graph_df = location_graph_df.append(df_middlepoint).reset_index(
        drop=True)
    fig = px.scatter_geo(location_graph_df,
                         lat=location_graph_df['Latitude'],
                         lon=location_graph_df['Longitude'],
                         hover_name=location_graph_df['City'])
    fig.update_layout(title='Cities and middle point')
    return fig


get_locations_map(Latitude, Longitude).show()
