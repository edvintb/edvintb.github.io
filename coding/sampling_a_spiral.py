import math
import random
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from matplotlib.patches import Polygon
from scipy.spatial import Voronoi
from scipy.optimize import linear_sum_assignment
from scipy.spatial.distance import cdist
from skimage.color import lab2rgb
import numpy as np

Sample = tuple[float, float]


def coord_to_color(coords: list[Sample]) -> list[tuple]:
    # rescale coords to [0,1]^2 by their bounding box, then map to CIELab a*b*
    # at fixed L*=70 and convert to sRGB. perceptually uniform: distance in
    # input space ~ perceived color distance, and averaging colors corresponds
    # to averaging the underlying coords.
    arr = np.asarray(coords, dtype=float)
    lo = arr.min(axis=0)
    hi = arr.max(axis=0)
    norm = (arr - lo) / np.where(hi - lo > 0, hi - lo, 1.0)
    L = np.full(len(arr), 70.0)
    a = (norm[:, 0] - 0.5) * 100
    b = (norm[:, 1] - 0.5) * 100
    lab = np.stack([L, a, b], axis=-1)[None, :, :]
    rgb = lab2rgb(lab)[0]
    return [tuple(c) for c in rgb]

def get_spiral_sample() -> Sample:
    # get a random sample
    t = random.uniform(0, 1)

    # parametrize the spiral
    angle = 2 * 2 * math.pi * t
    radius = 1 + 2 * t

    # convert to x-y coordinates
    x = math.cos(angle) * radius
    y = math.sin(angle) * radius

    return (x, y)


def get_gaussian_sample() -> Sample:
    # standard 2D gaussian centered at origin (variance 1 per axis)
    return (random.gauss(0, 1), random.gauss(0, 1))


def plot_samples(ax: Axes, num_samples: int):
    # get the samples
    samples: list[Sample] = [get_spiral_sample() for _ in range(num_samples)]

    # plot them
    xs = [s[0] for s in samples]
    ys = [s[1] for s in samples]
    ax.scatter(xs, ys, s=10, color="black")
    ax.set_aspect("equal")

    # extend axis limits beyond the plotted points
    margin = 1.5
    limit = max(max(abs(x) for x in xs), max(abs(y) for y in ys)) + margin
    ax.set_xlim(-limit, limit)
    ax.set_ylim(-limit, limit)

    # add gridlines
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.axhline(0, color="gray", linewidth=0.8)
    ax.axvline(0, color="gray", linewidth=0.8)


def _draw_knn_field(ax: Axes, points: list[Sample], colors: list[tuple], k: int,
                    bounds: tuple, resolution: int = 300):
    # for every pixel in a grid, color it by the mean of the k nearest training points' colors.
    xmin, xmax, ymin, ymax = bounds
    xs = np.linspace(xmin, xmax, resolution)
    ys = np.linspace(ymin, ymax, resolution)
    grid = np.stack(np.meshgrid(xs, ys), axis=-1).reshape(-1, 2)
    pts = np.array(points)
    cols = np.array(colors)
    dists = cdist(grid, pts)
    nn_idx = np.argpartition(dists, kth=k - 1, axis=1)[:, :k]
    img = cols[nn_idx].mean(axis=1).reshape(resolution, resolution, 3)
    img = np.clip(img, 0, 1)
    ax.imshow(img, extent=(xmin, xmax, ymin, ymax), origin="lower",
              alpha=0.4, interpolation="bilinear", zorder=0)


def _draw_grid_dots(ax_input: Axes, ax_output: Axes,
                    pairs: list[tuple[Sample, Sample]], k: int,
                    grid_size: int = 11):
    # plot a regular grid of black dots over the input cloud's bounding box,
    # and their k-NN-predicted locations as black dots on the output.
    train_x = np.array([p[0] for p in pairs])
    train_y = np.array([p[1] for p in pairs])
    lo = train_x.min(axis=0)
    hi = train_x.max(axis=0)
    xs_g = np.linspace(lo[0], hi[0], grid_size)
    ys_g = np.linspace(lo[1], hi[1], grid_size)
    gx, gy = np.meshgrid(xs_g, ys_g)
    queries = np.stack([gx.ravel(), gy.ravel()], axis=1)

    dists = cdist(queries, train_x)
    nn_idx = np.argpartition(dists, kth=k - 1, axis=1)[:, :k]
    pred = train_y[nn_idx].mean(axis=1)

    ax_input.scatter(queries[:, 0], queries[:, 1], c="black", s=5, zorder=5)
    ax_output.scatter(pred[:, 0], pred[:, 1], c="black", s=5, zorder=5)


def optimal_transport_pairs(pairs: list[tuple[Sample, Sample]]) -> list[tuple[Sample, Sample]]:
    # re-pair x's and y's to minimize sum of squared euclidean distances on
    # standardized coordinates (zero mean, unit variance per axis). this makes
    # the matching scale- and translation-invariant: it depends on the relative
    # shape of the two clouds, not on where they happen to live in R^2.
    xs = np.array([p[0] for p in pairs])
    ys = np.array([p[1] for p in pairs])
    xs_n = (xs - xs.mean(axis=0)) / xs.std(axis=0)
    ys_n = (ys - ys.mean(axis=0)) / ys.std(axis=0)
    cost = cdist(xs_n, ys_n, metric="sqeuclidean")
    row_ind, col_ind = linear_sum_assignment(cost)
    return [(tuple(xs[i]), tuple(ys[j])) for i, j in zip(row_ind, col_ind)]


def _draw_voronoi_cells(ax: Axes, points: list[Sample], colors: list[tuple], bounds: tuple):
    # add far-away points so every original point has a finite region
    xmin, xmax, ymin, ymax = bounds
    span = max(xmax - xmin, ymax - ymin)
    far = [
        (xmin - 100 * span, ymin - 100 * span),
        (xmax + 100 * span, ymin - 100 * span),
        (xmin - 100 * span, ymax + 100 * span),
        (xmax + 100 * span, ymax + 100 * span),
    ]
    vor = Voronoi(list(points) + far)

    for i in range(len(points)):
        region = vor.regions[vor.point_region[i]]
        if not region or -1 in region:
            continue
        polygon_pts = [vor.vertices[v] for v in region]
        ax.add_patch(Polygon(polygon_pts, facecolor=colors[i], alpha=0.6,
                             edgecolor="white", linewidth=0.8))


def plot_map(ax1: Axes, ax2: Axes, pairs: list[tuple[Sample, Sample]], k: int = 1,
             input_title: str = r"$X$  —  uniform on $[0,1]^2$",
             output_title: str = r"$Y = F(X)$  —  spiral"):
    # split into the two distributions
    input_samples = [p[0] for p in pairs]
    output_samples = [p[1] for p in pairs]

    # color each pair by its input coordinates via CIELab (perceptually uniform)
    colors = coord_to_color(input_samples)

    ux = [u[0] for u in input_samples]
    uy = [u[1] for u in input_samples]
    sx = [s[0] for s in output_samples]
    sy = [s[1] for s in output_samples]

    # symmetric square bounds around each cloud's bounding box, with a margin
    input_limit = max(max(abs(x) for x in ux), max(abs(y) for y in uy)) + 0.5
    output_limit = max(max(abs(x) for x in sx), max(abs(y) for y in sy)) + 1.5

    # input: voronoi cells (each input point is ground-truth training data, 1-NN region)
    _draw_voronoi_cells(ax1, list(zip(ux, uy)), colors,
                        (-input_limit, input_limit, -input_limit, input_limit))

    # colored sample dots on top
    ax1.scatter(ux, uy, c=colors, s=12, edgecolors="black", linewidths=0.4, zorder=4)
    ax2.scatter(sx, sy, c=colors, s=12, edgecolors="black", linewidths=0.4, zorder=4)

    # smaller black dots at grid coordinates and their pushforward in output
    _draw_grid_dots(ax1, ax2, pairs, k)

    # input axis
    ax1.set_xlim(-input_limit, input_limit)
    ax1.set_ylim(-input_limit, input_limit)
    ax1.set_aspect("equal")
    ax1.set_title(input_title, fontsize=14)

    # output axis: extended around origin
    ax2.set_xlim(-output_limit, output_limit)
    ax2.set_ylim(-output_limit, output_limit)
    ax2.set_aspect("equal")
    ax2.set_title(output_title, fontsize=14)

    # F arrow between the two axes
    # fig = ax1.figure
    # fig.text(0.5, 0.55, r"$F$", fontsize=22, ha="center", va="center")
    # fig.text(0.5, 0.48, r"$\longrightarrow$", fontsize=22, ha="center", va="center")

    # caption explaining the visualization
    # ax1.figure.text(0.5, 0.04,
    #          "Matching colors show how each input region maps to an output region under $F$.",
    #          fontsize=11, ha="center", va="center", style="italic", color="gray")


# we have samples from our data distribution
# we know it's a simple transform of a single random sample, but in theory it could be sth complicated

#### How do we learn the mapping into this distribution??

### A mapping between distributions is not well defined. There are infinite functions that push samples from one continuous distribution into samples from another. They will all do the job, but they are not all equally easy to learn. 

### To see this, imagine we have data ${y_i}_{i = 1}^{N}$. For each $y_i$, we sample $x_i$ from U(0, 1). This creates N pairs ${x_i, y_i}$. Our unknown $F$ should map $x_i \rightarrow y_i$. Let's start by parametrizing $F$ in a maximally flexible manner: for each $x \in X$, we have a unique parameter $\theta_x \in Y$ that decides the output value: $F(x) = \theta_x$. If we fit this function, the mapping is perfect for each ${x_i, y_i}$ and complete garbage everywhere else. We have created a lookup table without any generalization. This is the extreme of overfitting. Fundamentally, generalization requires sharing parameters across inputs. If each input has a unique parameter, there cannot be any generalization.

### While this is obviously a toy example, it serves as a useful starting point. From this starting point, what is the simplest way to introduce parameter sharing across inputs and start generalizing? What if we share the $\theta_{x_i}$ parameter across all inputs that are closer to $x_i$ than any other $x$? We return the value of the nearest neighbor in the training data. This is as flexible as the straight lookup, but also gives us some generalization. Let's see what this looks like.

## create pairs of samples from the uniform distribution in 2D and our spiral distribution. scatter plot the uniform samples on a 2d grid. color the grid by aligning each axis with the best possible set of two axis in color space. 

### we should use nearest neighbors here to illustrate the point. connect the made-up function to nearest neigbhor. k-NN really is a fundamental, maximally flexible algorithm.

### the logical flow I'm imagining is sth like this: Motivate generation as sampling. Motivate sampling as mapping one distribution into another. Motivate the use of the most flexible model with some amount of generalization -- nearest neighbors. Show that the inference becomes garbage when we move beyond k = 1. Explain this by talking about the infinite possible maps and the smoothness assumption we basically have to make when trying to generalize. Perhaps we can make a gif of a point moving around in the input space and see where it is being mapped to -- that could be quite cool actually. Perhaps we even talk about the pairings being the only design choice we have available to us here. 

### with enough data relative to the dimensionality of our space, we can make k-NN work. talk somewhat about curse of dimensionality and how the data required grows exponentially. This, in combination with high inference costs & no fundamental learning, motivates the use of more restrictive function families. In k-NN, our only design choice is the pairings we make. What is the next simplest step up from k-NN?

### Perhaps this is a blog post in itself...

### Make this more sensical by making "close" pairs. This is optimal transport. If we want to encode some underlying structure into parameters intead of doing this lookup thing, what is the simplest step in that direction?

### Then there are a few things: increasing the dimensionality of the input (is this required for sensible optimal transport? I think not, but let's check) and making the process multi-step. We can choose more parameters in a single step, or we can choose multi-step. Perhaps variational autoencoders fit in here somehow?

### there is also the choice of what our function tries to predict. velocity field? what are other options?

### Do GANs fit in anywhere?

### Perhaps random forest is the next step up from a k-nn algorithm? can we even use a random forest to map distributions to each other? Random forest is just a recipe (an algorithm) for taking data -> algorithm. so yes, this is possible. 

### and finally we get to diffusion... where we do a multi-step process with parameters shared across inputs. 

### First we can try a linear map... then we try a non-linear map (autoencoder)... then we talk about the O(N^3) optimal transport pairing algorithm and how we can avoid it --> learn a good pairing (variational autoencoder). Maybe our conclusion can be that models become "generative" when we introduce a pairing, a "latent variable"/per-datapoint parameter. VAE is learning the structure of the latent space instead of enforcing the optimal transport pairing. A normal autoencoder is similar to k-NN without the optimal transport paring. All euclidean directions are not important in high-dimensional space, so we can't just apply the OT algorithm, we instead learn the valuable directions of variation.

### VAEs are unable to really find the modes of the distribution. It predicts averages, and those averages fall of the manifold. The function that takes us all the way up the mode is too spiky/complicated for our parametrized family to express.

### GANs fail to capture diversity.

### How does it all fit together? All the mappings rely on a good pairing. A structure of our "latent space". Otherwise things become way too spiky. In a low-dim space, we can use the OT pairing. Then we do PCA/AE/VAE to learn a latent space. VAE learns a distribution over the latents. Does that concept exist in PCA/AE? Yes, this is the ordering. We explore different parametriazations of the mapping and show that a good pairing is important for all of them. Then we talk about how OT breaks down and learning a good set of latents instead.

### How does one transition into flow matching? We should do linear, non-linear, state stepping, velocity. Hopefully we can show that a state-stepping model can achieve the same with fewer params, and then modeling velocity allows using fewer params still. Perhaps the state-stepping and velocity models are already learning the latent space? it's a little unclear how the flows learn the right latent structure -- perhaps the noise is simply the closest at that point and that is our latent structure. 

### Are there other ways of learning a distribution other than the ability to sample from it? I guess the ability to sample is an implicit model of the distribution. We can't plug values in and get probabilities out. But we can sample it.

### 

### we connect two points. We can use k-NN to effectively recreate the datapoint as soon as we have some signal. Instead of having one parameter per input, 

### the biggest problem when trying to understand a new field is the "why?". What was motivation behind the progression? The "why?" makes things come alive. Stories is how we form memories.


def _draw_input_panel(ax: Axes, input_samples: list[Sample],
                      colors: list[tuple]):
    ux = [u[0] for u in input_samples]
    uy = [u[1] for u in input_samples]
    input_limit = max(max(abs(x) for x in ux), max(abs(y) for y in uy)) + 0.5
    _draw_voronoi_cells(ax, list(zip(ux, uy)), colors,
                        (-input_limit, input_limit, -input_limit, input_limit))
    ax.scatter(ux, uy, c=colors, s=12, edgecolors="black", linewidths=0.4, zorder=4)
    ax.set_xlim(-input_limit, input_limit)
    ax.set_ylim(-input_limit, input_limit)
    ax.set_aspect("equal")
    ax.set_title(r"$Z$ $\sim$ U$(-2,2)^2$", fontsize=14)


def _draw_output_panel(ax: Axes, output_samples: list[Sample],
                       colors: list[tuple]):
    sx = [s[0] for s in output_samples]
    sy = [s[1] for s in output_samples]
    output_limit = max(max(abs(x) for x in sx), max(abs(y) for y in sy)) + 1.5
    ax.scatter(sx, sy, c=colors, s=12, edgecolors="black", linewidths=0.4, zorder=4)
    ax.set_xlim(-output_limit, output_limit)
    ax.set_ylim(-output_limit, output_limit)
    ax.set_aspect("equal")
    ax.set_title(r"$X$ $\sim$ $p_{\mathrm{data}}$", fontsize=14)


def _scatter_panel(ax: Axes, samples: list[Sample], margin: float):
    xs = [s[0] for s in samples]
    ys = [s[1] for s in samples]
    lim = max(max(abs(x) for x in xs), max(abs(y) for y in ys)) + margin
    ax.scatter(xs, ys, c="black", s=8)
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_aspect("equal")


def render_data_figure(spiral_x: list[Sample]):
    # raw data samples on a white background
    fig, ax = plt.subplots(figsize=(6, 6))
    _scatter_panel(ax, spiral_x, margin=1.5)
    return fig


def render_predictors_figure(uniform_z: list[Sample]):
    # raw predictor samples on a white background
    fig, ax = plt.subplots(figsize=(6, 6))
    _scatter_panel(ax, uniform_z, margin=0.5)
    return fig


def render_training_figure(uniform_pairs: list[tuple[Sample, Sample]]):
    # 1x2: predictor Z with voronoi cells colored by position, alongside the
    # data X recolored by their (random) paired predictor. matching colors
    # show the pairing from z_i to x_i.
    fig, axd = plt.subplot_mosaic([["Z", "X"]], figsize=(12, 6))

    input_samples = [p[0] for p in uniform_pairs]
    output_samples = [p[1] for p in uniform_pairs]
    colors = coord_to_color(input_samples)

    _draw_input_panel(axd["Z"], input_samples, colors)
    _draw_output_panel(axd["X"], output_samples, colors)
    return fig


def render_inference_figure(pairs: list[tuple[Sample, Sample]],
                            num_queries: int = 200,
                            ks: tuple = (1, 3, 5, 10)):
    # 2x3 grid with Z spanning both rows of the leftmost column, and the four
    # k-NN output panels filling the right 2x2. swap `pairs` for OT-paired
    # pairs to see the inference behavior under an OT mapping.
    assert len(ks) == 4, "this 2x3 layout assumes exactly 4 values of k"
    k_a, k_b, k_c, k_d = ks
    layout = [
        ["Z", f"k{k_a}", f"k{k_b}"],
        ["Z", f"k{k_c}", f"k{k_d}"],
    ]
    panel = 7
    fig, axd = plt.subplot_mosaic(
        layout, figsize=(panel * 3, panel * 2),
    )

    train_z = np.array([p[0] for p in pairs])
    train_x = np.array([p[1] for p in pairs])
    train_z_list = [tuple(z) for z in train_z]
    cell_colors = coord_to_color(train_z_list)

    # new queries from the same U(-2, 2)^2 distribution
    queries = np.array([
        (random.uniform(-2, 2), random.uniform(-2, 2)) for _ in range(num_queries)
    ])

    # match the training input-panel limit (computed from training Z)
    z_lim = max(float(np.abs(train_z).max()), 2.0) + 0.5
    _draw_voronoi_cells(axd["Z"], train_z_list, cell_colors,
                        (-z_lim, z_lim, -z_lim, z_lim))
    axd["Z"].scatter(queries[:, 0], queries[:, 1], c="black", s=10, zorder=4)
    axd["Z"].set_xlim(-z_lim, z_lim)
    axd["Z"].set_ylim(-z_lim, z_lim)
    axd["Z"].set_aspect("equal")
    axd["Z"].set_title(r"$Z$ $\sim$ U$(-2,2)^2$", fontsize=14)

    # match the training output-panel limit
    x_lim = float(np.abs(train_x).max()) + 1.5

    dists = cdist(queries, train_z)
    for k in ks:
        nn_idx = np.argpartition(dists, kth=k - 1, axis=1)[:, :k]
        pred = train_x[nn_idx].mean(axis=1)
        ax = axd[f"k{k}"]
        ax.scatter(pred[:, 0], pred[:, 1], c="black", s=10)
        ax.set_xlim(-x_lim, x_lim)
        ax.set_ylim(-x_lim, x_lim)
        ax.set_aspect("equal")
        ax.tick_params(labelleft=False)
        ax.set_title(rf"$k={k}$", fontsize=14)
    return fig


def render_all_figures(uniform_pairs: list[tuple[Sample, Sample]]):
    # returns the figures in a stable order with stable filenames so callers
    # can iterate and either show, save, or both.
    spiral_x = [p[1] for p in uniform_pairs]
    uniform_z = [p[0] for p in uniform_pairs]
    return [
        ("data",             render_data_figure(spiral_x)),
        ("predictors",       render_predictors_figure(uniform_z)),
        ("training",         render_training_figure(uniform_pairs)),
        ("inference_random", render_inference_figure(uniform_pairs)),
        ("inference_ot",     render_inference_figure(
            optimal_transport_pairs(uniform_pairs))),
    ]


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--save-dir", type=str, default=None,
                        help="if set, save each figure as a PNG under this dir "
                             "(no GUI window). otherwise plt.show().")
    parser.add_argument("--seed", type=int, default=None,
                        help="optional RNG seed for reproducibility")
    parser.add_argument("-n", type=int, default=500,
                        help="number of samples for each distribution")
    args = parser.parse_args()

    if args.seed is not None:
        random.seed(args.seed)
        np.random.seed(args.seed)

    # generate the dataset once and reuse the same samples across every figure,
    # mirroring how a real model is trained on a single fixed dataset.
    N = args.n
    spiral_x = [get_spiral_sample() for _ in range(N)]
    uniform_z = [(random.uniform(-2, 2), random.uniform(-2, 2)) for _ in range(N)]
    uniform_pairs = list(zip(uniform_z, spiral_x))

    figures = render_all_figures(uniform_pairs)

    if args.save_dir:
        import os
        os.makedirs(args.save_dir, exist_ok=True)
        for name, fig in figures:
            path = os.path.join(args.save_dir, f"{name}.png")
            fig.savefig(path, dpi=150, bbox_inches="tight")
            print(f"saved {path}")
    else:
        plt.show()
