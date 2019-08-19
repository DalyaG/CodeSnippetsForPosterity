
import subprocess
import numpy as np
from haversine import haversine
from optparse import OptionParser
from math import sqrt, pow, atan2, degrees, pi
from shapely import affinity
from shapely.geometry import LineString

R_EARTH = 6371000

def Main():
    """
    Input 2 lat-lng points and a joint-radius, to draw an ellipse around these two centers.
    NOTE:
        The joint-radius should be at least as large at the distance between the two points.

    Example command:

    python plot_ellipse.py --p1_lat 32.076761 --p1_lng 34.792510 --p2_lat 32.083257 --p2_lng 34.767737 -r 3000

    In details:
    1. From the lat-lng get ellipse parameters.
    2. Draw ellipse around the origin (0,0) measured in meters.
    3. Move this ellipse to be centered around the input centers.
    4. Open browser tab with ellipse in s2map.
    """
    parser = OptionParser()
    parser.add_option("--p1_lat")
    parser.add_option("--p1_lng")
    parser.add_option("--p2_lat")
    parser.add_option("--p2_lng")
    parser.add_option("-r", "--radius_in_meters")
    parser.add_option("-n", "--num_points")
    options, _ = parser.parse_args()

    num_points = int(options.num_points) if options.num_points is not None else 20
    p1_lat, p1_lng = float(options.p1_lat), float(options.p1_lng)
    p2_lat, p2_lng = float(options.p2_lat), float(options.p2_lng)
    radius_in_meters = float(options.radius_in_meters)

    a, b = GetEllipseAxisLengths(p1_lat, p1_lng, p2_lat, p2_lng, radius_in_meters)
    perimeter_points_in_meters = GetEllipsePointInMeters(a, b, num_points)
    points = GetEllipsePoints(p1_lat, p1_lng, p2_lat, p2_lng, perimeter_points_in_meters)
    OpenS2Map(points)


def GetEllipseAxisLengths(p1_lat, p1_lng, p2_lat, p2_lng, radius_in_meters):
    d = haversine((p1_lat, p1_lng), (p2_lat, p2_lng)) * 1000.0
    if radius_in_meters < d:
        raise ValueError("Please specify radius larger than the distance between the two input points.")
    a = radius_in_meters / 2.0
    b = sqrt(pow(a, 2) - pow(d / 2.0, 2))
    return a, b

def GetEllipsePointInMeters(a, b, num_points):
    """
    :param a: length of "horizontal" axis in meters
    :param b: length of "vertical" axis in meters
    :param num_points: number of points to draw on each side of the ellipse
    :return: List of tuples of perimeter points on the ellipse, centered around (0,0), in m.
    """
    x_points = list(np.linspace(-a, a, num_points))[1:-1]
    y_points_pos = [sqrt(pow(a, 2) - pow(x, 2)) * (float(b) / float(a))
                    for x in x_points]
    y_points_neg = [-y for y in y_points_pos]

    perimeter_points_in_meters = [tuple([-a, 0])] + \
                                 [tuple([x, y]) for x, y in zip(x_points, y_points_pos)] + \
                                 [tuple([a, 0])] + \
                                 list(reversed([tuple([x, y]) for x, y in zip(x_points, y_points_neg)]))
    return perimeter_points_in_meters

def GetEllipsePoints(p1_lat, p1_lng, p2_lat, p2_lng, perimeter_points_in_meters):
    """
    Enter ellipse centers in lat-lng and ellipse perimeter points around the origin (0,0),
    and get points on the perimeter of the ellipse around the centers in lat-lng.
    :param p1_lat: lat coordinates of center point 1
    :param p1_lng: lng coordinates of center point 1
    :param p2_lat: lat coordinates of center point 2
    :param p2_lng: lng coordinates of center point 2
    :param perimeter_points_in_meters: List of tuples of perimeter points on the ellipse, centered around (0,0), in m.
    :return:
    """
    center_lng = (p1_lng + p2_lng) / 2.0
    center_lat = (p1_lat + p2_lat) / 2.0
    perimeter_points_in_lng_lat = [AddMetersToPoint(center_lng, center_lat, p[0], p[1])
                                   for p in perimeter_points_in_meters]
    ellipse = LineString(perimeter_points_in_lng_lat)

    angle = degrees(atan2(p2_lat - p1_lat, p2_lng - p1_lng))
    ellipse_rotated = affinity.rotate(ellipse, angle)

    ellipse_points_lng_lat = list(ellipse_rotated.coords)
    ellipse_points = [tuple([p[1], p[0]]) for p in ellipse_points_lng_lat]
    return ellipse_points

def AddMetersToPoint(center_lng, center_lat, dx, dy):
    """
    :param center_lng, center_lat: GPS coordinates of the center between the two input points.
    :param dx: distance to add to x-axis (lng) in meters
    :param dy: distance to add to y-axis (lat) in meters
    """
    new_x = center_lng + (dx / R_EARTH) * (180 / pi) / np.cos(center_lat * pi/180)
    new_y = center_lat + (dy / R_EARTH) * (180 / pi)
    return tuple([new_x, new_y])

def OpenS2Map(points):
    url = "http://s2map.com/#order=latlng&mode=polygon&s2=false&points={}".format(str(points).replace(" ", ","))
    cmd = ["python", "-m", "webbrowser", "-t", url]
    subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT).communicate()


if __name__ == '__main__':
    Main()
