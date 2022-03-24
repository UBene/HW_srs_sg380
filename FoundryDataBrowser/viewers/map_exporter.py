"""
Created on Mar 17, 2022

@author: Benedikt Ursprung
"""
from ScopeFoundry.logged_quantity import LQCollection
from qtpy import QtWidgets
import time
from pyqtgraph import dockarea
from FoundryDataBrowser.viewers.image_processor import ImageManager


class MapExporter:
    def __init__(self, image_manager: ImageManager):

        S = self.settings = LQCollection()
        S.New("include_scale_bar", bool, initial=True)
        S.New("scale_bar_width", float, initial=1, spinbox_decimals=3)
        S.New("scale_bar_text", str, ro=False)

        self.image_manager = image_manager

    def new_widget(self):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)

        layout.addWidget(self.settings.New_UI())

        self.jpegs_pushButton = QtWidgets.QPushButton("export maps as jpegs")
        layout.addWidget(self.jpegs_pushButton)
        self.jpegs_pushButton.clicked.connect(self.all_image_as_jpegs)

        self.current_as_jpg_pushButton = QtWidgets.QPushButton("current as jpegs")
        layout.addWidget(self.current_as_jpg_pushButton)
        self.jpegs_pushButton.clicked.connect(self.all_image_as_jpegs)

    def new_dock(self):
        return dockarea.Dock(name="exporter", widget=self.new_widget())

    def all_image_as_jpegs(self):
        for name, image in self.image_manager.images.items():
            self.image_as_jpeg(name, image)

    def current_image_as_jpeg(self):
        name = self.image_manager.settings.image.val
        image = self.image_manager[name]
        self.image_as_jpeg(name, image)

    def image_as_jpeg(self, name, image, cmap="gist_heat"):
        import matplotlib.pylab as plt

        plt.figure(dpi=200)
        plt.title(name)
        ax = plt.subplot(111)
        Ny, Nx = image.shape
        extent = [0, self.unit_per_px * Nx, 0, self.unit_per_px * Ny]
        plt.imshow(
            image, origin="lower", interpolation=None, cmap=cmap, extent=extent,
        )

        ES = self.map_export_settings
        if ES["include_scale_bar"]:
            add_scale_bar(ax, ES["scale_bar_width"], ES["scale_bar_text"])
        cb = plt.colorbar()
        plt.tight_layout()
        fig_name = self.fname.replace(
            ".h5", "_{:0.0f}_{}.jpg".format(time.time(), name)
        )
        plt.savefig(fig_name)
        plt.close()


def add_scale_bar(
    ax,
    width=0.005,
    text=True,
    d=None,
    height=None,
    h_pos="left",
    v_pos="bottom",
    color="w",
    edgecolor="k",
    lw=1,
    set_ticks_off=True,
    origin_lower=True,
    fontsize=13,
):
    from matplotlib.patches import Rectangle
    import matplotlib.pylab as plt

    imshow_ticks_off_kwargs = dict(
        axis="both",
        which="both",
        left=False,
        right=False,
        bottom=False,
        top=False,
        labelbottom=False,
        labeltop=False,
        labelleft=False,
        labelright=False,
    )
    """
        places a rectancle onto the axis *ax.
        d is the distance from the edge to rectangle.
    """

    x0, y0 = ax.get_xlim()[0], ax.get_ylim()[0]
    x1, y1 = ax.get_xlim()[1], ax.get_ylim()[1]

    Dx = x1 - x0
    if d == None:
        d = Dx / 18.0
    if height == None:
        height = d * 0.8
    if width == None:
        width = 5 * d

    if h_pos == "left":
        X = x0 + d
    else:
        X = x1 - d - width

    if origin_lower:
        if v_pos == "bottom":
            Y = y0 + d
        else:
            Y = y1 - d - height
    else:
        if v_pos == "bottom":
            Y = y0 - d - height
        else:
            Y = y1 + d

    xy = (X, Y)

    p = Rectangle(xy, width, height, color=color, ls="solid", lw=lw, ec=edgecolor)
    ax.add_patch(p)

    if text:
        if type(text) in [bool, None] or text == "auto":
            text = str(int(width * 1000)) + " \u03BCm"
            print("caution: Assumes extent to be in mm, set text arg manually!")
        if v_pos == "bottom":
            Y_text = Y + 1.1 * d
            va = "bottom"
        else:
            Y_text = Y - 0.1 * d
            va = "top"
        txt = plt.text(
            X + 0.5 * width,
            Y_text,
            text,
            fontdict={
                "color": color,
                "weight": "heavy",
                "size": fontsize,
                # 'backgroundcolor':edgecolor,
                "alpha": 1,
                "horizontalalignment": "center",
                "verticalalignment": va,
            },
        )
        import matplotlib.patheffects as PathEffects

        txt.set_path_effects(
            [PathEffects.withStroke(linewidth=lw, foreground=edgecolor)]
        )

    if set_ticks_off:
        ax.tick_params(**imshow_ticks_off_kwargs)
