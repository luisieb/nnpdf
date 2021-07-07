"""
    Target functions to minimize during hyperparameter scan

    All functions in this module have the same signature:
        fold_losses: list of loss-per-fold
        **kwargs

    New loss functions can be added directly in this module
    the name in the runcard must match the name in the module

    Example
    -------
    >>> import n3fit.hyper_optimization.rewards
    >>> f = ["average", "best_worst", "std"]
    >>> losses = [2.34, 1.234, 3.42]
    >>> for fname in f:
    >>>    fun = getattr(n3fit.hyper_optimization.rewards, fname) 
    >>>    print(f"{fname}: {fun(losses, None):2.4f}")
    average: 2.3313
    best_worst: 3.4200
    std: 0.8925

"""
import numpy as np
from validphys.pdfgrids import xplotting_grid, distance_grids


def average(fold_losses, **kwargs):
    """Returns the average of fold losses"""
    return np.average(fold_losses)


def best_worst(fold_losses, **kwargs):
    """Returns the maximum loss of all k folds"""
    return np.max(fold_losses)


def std(fold_losses, **kwargs):
    """Return the standard dev of the losses of the folds"""
    return np.std(fold_losses)


def fit_distance(fold_losses, n3pdfs=None, **kwargs):
    """Loss function for hyperoptimization based on the distance of
    the fits of all folds to the first fold
    """
    if n3pdfs is None:
        raise ValueError("fit_distance needs n3pdf models to act upon")
    xgrid = np.concatenate([np.logspace(-6, -1, 20), np.linspace(0.11, 0.9, 30)])
    plotting_grids = [xplotting_grid(pdf, 1.6, xgrid) for pdf in n3pdfs]
    distances = distance_grids(n3pdfs, plotting_grids, 0)
    # The first distance will obviously be 0
    # TODO: define this more sensibly, for now it is just a template
    max_distance = 0
    for distance in distances:
        max_distance = max(max_distance, distance.grid_values.max())
    return max_distance


def _set_central_value(n3pdf, model):
    """Given an N3PDF object and a MetaModel, set the PDF_0 layer
    to be the central value of the n3pdf object"""
    # Get the input x
    for key, grid in model.x_in.items():
        if key != "integration_grid":
            input_x = grid.numpy()
            break

    # Compute the central value of the PDF
    full_pdf = n3pdf(input_x)
    cv_pdf = op.numpy_to_tensor(np.mean(full_pdf, axis=0, keepdims=True))

    def central_value(x, training=None):
        return cv_pdf

    model.get_layer("PDF_0").call = central_value
    # This model won't be trainable ever again
    model.trainable = False
    model.compile()


def fit_future_tests(fold_losses, n3pdfs=None, experimental_models=None, **kwargs):
    """Use the future tests as a metric for hyperopt

    NOTE: this function should only be called once at the end of
    every hyperopt iteration, as it is destructive for the models
    """
    if n3pdfs is None:
        raise ValueError("fit_future_test needs n3pdf models to act upon")
    if experimental_models is None:
        raise ValueError("fit_future_test needs experimental_models to compute chi2")

    from n3fit.backends import MetaModel
    from n3fit.backends import operations as op

    # For the last model (the one containing all data) the PDF covmat doesn't need to be computed
    # but the mask needs to be flipped in the folding for the appropiate datasets
    last_model = experimental_models[-1]
    _set_central_value(n3pdfs[-1], last_model)

    # Loop over all models but the last (our reference!)
    total_loss = 0.0
    for n3pdf, exp_model in zip(n3pdfs[:-1], experimental_models[:-1]):

        _set_central_value(n3pdf, exp_model)

        # Get the full input and the total chi2
        full_input = exp_model.input
        exp_chi2 = exp_model.compute_losses()["loss"][0]

        # Now update the loss with the PDF covmat
        for layer in exp_model.get_layer_re(".*_exp$"):
            # Get the input to the loss layer
            model_output = MetaModel(full_input, layer.input)
            # Get the full predictions and generate the PDF covmat
            y = model_output.predict()[0]  # The first is a dummy-dim
            pdf_covmat = np.cov(y, rowvar=False)
            # Update the covmat of the loss
            layer.add_covmat(pdf_covmat)
            # Update the mask of the last_model so that its syncthed with this layer
            last_model.get_layer(layer.name).update_mask(layer.mask)

        # Compute the loss with pdf errors
        pdf_chi2 = exp_model.compute_losses()["loss"][0]

        # And the loss of the best (most complete) fit
        best_chi2 = last_model.compute_losses()["loss"][0]

        # Now make this into a measure of the total loss
        # for instance, any deviation from the "best" value is bad
        total_loss += np.abs(best_chi2 - pdf_chi2)

    return total_loss
