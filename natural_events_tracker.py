import requests
from matplotlib import pyplot as plt
import geopandas as gpd
import pandas as pd
import io
from PIL import Image, ImageFont, ImageDraw


"""
Const variables
"""
MAIN_URL = "https://eonet.gsfc.nasa.gov/api/v3/events"
COLORS = ["red", "blue", "yellow", "green", "violet", "rose", "orange", "cyan"]


class GetDataError(Exception):
    """
    Exception for handling failed connection to database
    """

    def __init__(self, message="Can not get data from server!"):
        super().__init__(self, message)


class OpenImageError(Exception):
    """
    Exception for handling failure to open and
    create Image using Pillow library
    """

    def __init__(self, message="Can not open map!"):
        super().__init__(self, message)


class TooManyCatError(Exception):
    """
    Exception for handling too many event categories (>=9)
    """

    def __init__(
        self,
        mess="Too many categories. Please decrease number of days!",
    ):
        super().__init__(self, mess)


class Event:
    """
    A class to represent single event in from database

    Attributes
    ----------
    category : str
        represent a category of event by it's id
    x : floats list
        represent event's longitude coordinates
    y : floats list
        represent event's latitude coordinates
    value : floats list
        represent magnitude values of event
        could also have null values

    """

    def __init__(self, category, x, y, value):
        self._category = category
        self._x = x
        self._y = y
        self._value = value

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, val):
        self._x = val

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, val):
        self._y = val

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, val):
        self._value = val

    @property
    def category(self):
        return self._category

    @category.setter
    def category(self, val):
        self._category = val


class EventTracker:
    """
    A class to represent a EventTracker which manages the program

    Attributes
    ----------
    events :
        contains list of Events objects
    classified_events :
        contains dictonary of Events based on category
    """

    def __init__(self, days=None):
        """
        Constructs all the necessary attributes objects by calling methods.
        """
        self.events = self.get_events(days)
        self.classified_events = self.get_classified_events()

    def get_events(self, days=None):
        """
        Takes as parameter number of days from which we take data
        call methods to get data and to  make list of Events objects

        returns list of Events objects
        """
        url = MAIN_URL
        if days is not None:
            url += "?days=" + str(days)
        data = self.get_data(url)
        events = self.create_events(data["events"])
        return events

    def get_data(self, url):
        """
        Takes as parameter url and returns all data from database
        """
        try:
            return requests.get(url).json()
        except Exception:
            raise GetDataError()

    def create_events(self, events_data):
        """
        Takes as parameter all data from database,
        iterates through and gets Event attributes.
        Create Events obejcts from this attributes and
        returns list of those Events
        """
        events = []
        for event in events_data:
            x = []
            y = []
            value = []
            for geo in event["geometry"]:
                x.append(geo["coordinates"][0])
                y.append(geo["coordinates"][1])
                value.append(geo["magnitudeValue"])
            creted_event = Event(event["categories"][0]["id"], x, y, value)
            events.append(creted_event)
        return events

    def get_classified_events(self):
        """
        Iterates through Events objects and makes dictonary of events where
        keys are event's category
        returns this dictonary
        """
        events_dict = {}
        for event in self.events:
            if event.category not in events_dict.keys():
                events_dict[event.category] = [event]
            else:
                events_dict[event.category].append(event)

        if len(list(events_dict.keys())) >= 9:
            raise TooManyCatError

        return events_dict

    def get_radius_for_category(self, value_list):
        """
        Support method for method normalise_events_values. It iterates through
        list of values and returns minimal and maximal values.
        If there are only nulls in the list returns None
        """
        values = []
        for value in value_list:
            if value is not None:
                values.append(value)
        values.sort()
        if len(values) > 1:
            max = values[len(values) - 1]
            mini = values[0]
            return mini, max
        return None

    def calc_dist(self, x, y, x_neib, y_neib):
        """
        Support method for method intensity. I
        It returns 2D distance between two 2D points.
        """
        distance = ((x - x_neib) ** 2 + (y - y_neib) ** 2) ** 0.5
        return distance

    def intensity(self, x_coords, y_coords, values):
        """
        Takes as parameters 3 lists of points features.
        Method for each point finds all points closer than specific distance
        and creates new point which has average position of found points
        and summed up value. If some points are left, they are added
        without any changes.
        It returns 3 lists which represents new points
        """

        new_points_x, new_points_y, new_points_value = [], [], []
        used = [0 for x in range(len(x_coords))]
        i = 0
        for x, y, value in zip(x_coords, y_coords, values):
            if used[i] != 0:
                continue
            j = 0
            neibours_x, neibours_y, neibours_value = [], [], []
            for x_neib, y_neib, value_neib in zip(x_coords, y_coords, values):
                if used[i] != 0:
                    continue
                if i != j:
                    distance = self.calc_dist(x, y, x_neib, y_neib)
                    if distance < 60:
                        neibours_x.append(x_neib)
                        neibours_y.append(y_neib)
                        neibours_value.append(value_neib)

                        used[j] = 1
                j += 1

            if len(neibours_x) > 0:
                avg_x = (x + sum(neibours_x)) / (len(neibours_x) + 1)
                avg_y = (y + sum(neibours_y)) / (len(neibours_y) + 1)
                avg_value = value + sum(neibours_value)
                new_points_x.append(avg_x)
                new_points_y.append(avg_y)
                new_points_value.append(avg_value)
                used[i] = 1
            i += 1

        for x, y, value, use in zip(x_coords, y_coords, values, used):
            if use == 0:
                new_points_x.append(x)
                new_points_y.append(y)
                new_points_value.append(value)

        return new_points_x, new_points_y, new_points_value

    def normalise_events_values(self, value_list):
        """
        Takes as parameters list of point values
        Method calls get_radius_for_category and then creates new list of
        point where values we have are const instead of nulls and
         from a specific range for not nulls
        It returns new list
        """
        normalised_values = []
        mini_max = self.get_radius_for_category(value_list)
        for value in value_list:
            if value is not None and mini_max is not None:
                normalised_value = (
                    400 * (int)(value - mini_max[0]) / (mini_max[1] - mini_max[0]) + 20
                )
                normalised_values.append(normalised_value)
            else:
                normalised_values.append(250)
        return normalised_values

    def get_coords(self, checked_params, intensify):
        """
        Takes as parameters boolean list which indicates event categories that
        should be on plot and boolean value intensify
        which indicates if close points should be connected.
        Method for each event category (which was True in boolean list)
        iterates through coordinates in all events and
        adds all features: x-coords, y-coords, point-value to lists.
        Then calls normalise_events_values method which makes all values
        for points appropriate.
        Then depanding on boolean can call intensity.
        It returns dictonary of keys category events and values of
        lists of points features
        """
        all_coords = {}
        j = -1
        for category in self.classified_events.keys():
            j += 1
            if not checked_params[j]:
                continue
            single_category_geometries = {}
            x_list = []
            y_list = []
            value_list = []

            for event in self.classified_events[category]:
                for x, y, value in zip(event.x, event.y, event.value):
                    x_list.append(x)
                    y_list.append(y)
                    value_list.append(value)
            normalised_values = self.normalise_events_values(value_list)

            if intensify:
                x_list, y_list, normalised_values = self.intensity(
                    x_list, y_list, normalised_values
                )

            single_category_geometries["value"] = normalised_values
            single_category_geometries["x"] = x_list
            single_category_geometries["y"] = y_list
            all_coords[category] = single_category_geometries
        return all_coords

    def add_legend(self, background, map_width, map_height, event_types):
        """
        parameters:
        background:
            Image objects which contains object world
            map with empty space for legend
        map_width, map_height:
            Image width and height
        event_types:
            List of event categories

        Method iterates through event categories and for each
        chooses text features and adds category name as text
        in suitable place on Image
        """
        for i in range(len(event_types)):
            caption = event_types[i]
            font = ImageFont.truetype(font="fonts/arial.ttf", size=30)
            w, h = font.getsize(caption)
            draw = ImageDraw.Draw(background)
            text_position_coeff = (i - (int)(len(event_types) / 2)) / len(event_types)
            draw.text(
                (
                    (map_width - w) / 2 - map_width / 2 * text_position_coeff,
                    (map_height + 100 + (-h - 100) / 2),
                ),
                caption,
                font=font,
                fill=COLORS[i],
            )

    def open_as_image(self, all_coords, save):
        """
        parameters:
        Dictonary which contains points parameters sorted by category

        Boolean save which indicates if we save output to .png file

        Method creates empty image using PIL, pastes plot to it and adds
        legend to the plot. Can also save the image, then shows it for user
        """
        img_buf = io.BytesIO()
        plt.savefig(img_buf, format="png")
        try:
            im = Image.open(img_buf)
            map_width, map_height = im.size
            background = Image.new("RGBA", (map_width, map_height + 100), color="white")
            background.paste(im, (0, 0, map_width, map_height))
            self.add_legend(background, map_width, map_height, list(all_coords.keys()))
        except Exception:
            raise OpenImageError()
        if save:
            background.save("natural_events.png")
        background.show()

    def create_map(self, all_coords, make_png=False, save=False):
        """
        parameters:

        Dictonary which contains points parameters sorted by category
        which looks like this:
        {'cat1':{'x':[x1], 'y': [y1], 'value': [value1]}

        Boolean make_png which indicates if
        we make_png file or a plot using pyplot

        Boolean save which indicates if we save output to .png file

        Method close all active figures, calls methods to create world max,
        add points to plot and base on parameters creates plot
        with adding legend and showing the plot)
        or png image and saves it or not
        """
        plt.close()
        ax = self.create_empty_map()
        self.add_points_to_plot(ax, all_coords)

        if make_png:
            self.open_as_image(all_coords, save)
        else:
            plt.legend(
                loc="lower center",
                bbox_to_anchor=(0.5, -0.1),
                fancybox=True,
                shadow=True,
                ncol=8,
            )
            if save:
                plt.savefig("natural_events.png")
            plt.show()

    def create_empty_map(self):
        """
        Creates empty world map ussing geopandas dataset
        and returns ax of this plot
        """
        world = gpd.read_file(gpd.datasets.get_path("naturalearth_lowres"))
        fig, ax = plt.subplots(figsize=(20, 10))
        world.plot(ax=ax)
        return ax

    def add_points_to_plot(self, ax, all_coords):
        """
        Iterates through categories of events and makes DataFrame for each of
        them which then transform into GeoDataFrame and adds it as series of
        data to the chart
        """
        i = 0
        for category_name, category in all_coords.items():
            df = pd.DataFrame(
                {
                    "x": category["x"],
                    "y": category["y"],
                    "size": category["value"],
                }
            )
            gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.x, df.y))
            gdf.plot(
                ax=ax,
                marker="o",
                color=COLORS[i],
                markersize="size",
                alpha=1.0,
                label=category_name,
            )
            i += 1
