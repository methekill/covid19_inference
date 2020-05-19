# ------------------------------------------------------------------------------ #
# @Author:        F. Paul Spitzner
# @Email:         paul.spitzner@ds.mpg.de
# @Created:       2020-05-19 12:00:32
# @Last Modified: 2020-05-19 12:01:20
# ------------------------------------------------------------------------------ #

# utility.py
# add model argument
# var names argument and defaults
# if model.is_hierc.: ... make this apply only to the hierarchical case and check before
# remove w parameter
def hierarchical_normal(
    name,
    name_sigma,
    pr_mean,
    pr_sigma,
    len_L2,
    w=1.0,
    error_fact=2.0,
    error_cauchy=True,
):
    r"""
        Implements an hierarchical normal model:

        .. math::

            x_\text{L1} &= Normal(\text{pr\_mean}, \text{pr\_sigma})\\
            y_{i, \text{L2}} &= Normal(x_\text{L1}, \sigma_\text{L2})\\
            \sigma_\text{L2} &= HalfCauchy(\text{error\_fact} \cdot \text{pr\_sigma})

        It is however implemented in a non-centered way, that the second line is changed to:

         .. math::

            y_{i, \text{L2}} &= x_\text{L1} +  Normal(0,1) \cdot \sigma_\text{L2}

        See for example https://arxiv.org/pdf/1312.0906.pdf


        Parameters
        ----------
        name : str
            Name under which :math:`x_\text{L1}` and :math:`y_\text{L2}` saved in the trace. ``'_L1'`` and ``'_L2'``
            is appended
        name_sigma : str
            Name under which :math:`\sigma_\text{L2}` saved in the trace. ``'_L2'`` is appended.
        pr_mean : float
            Prior mean of :math:`x_\text{L1}`
        pr_sigma : float
            Prior sigma for :math:`x_\text{L1}` and (muliplied by ``error_fact``) for :math:`\sigma_\text{L2}`
        len_L2 : int
            length of :math:`y_\text{L2}`
        error_fact : float
            Factor by which ``pr_sigma`` is multiplied as prior for `\sigma_\text{L2}`
        error_cauchy : bool
            if False, a :math:`HalfNormal` distribution is used for :math:`\sigma_\text{L2}` instead of :math:`HalfCauchy`

        Returns
        -------
        y : :class:`~theano.tensor.TensorVariable`
            the random variable :math:`y_\text{L2}`
        x : :class:`~theano.tensor.TensorVariable`
            the random variable :math:`x_\text{L1}`

    """
    if not len_L2:  # not hierarchical
        Y = pm.Normal(name, mu=pr_mean, sigma=pr_sigma)
        X = None

    else:
        w = 1.0
        if error_cauchy:
            sigma_Y = pm.HalfCauchy(name_sigma + "_L2", beta=error_fact * pr_sigma)
        else:
            sigma_Y = pm.HalfNormal(name_sigma + "_L2", sigma=error_fact * pr_sigma)

        X = pm.Normal(name + "_L1", mu=pr_mean, sigma=pr_sigma)
        phi = pm.Normal(
            name + "_L2_raw", mu=0, sigma=1, shape=len_L2
        )  # (1-w**2)*sigma_X+1*w**2, shape=len_Y)
        Y = w * X + phi * sigma_Y
        pm.Deterministic(name + "_L2", Y)

    return Y, X


# utility.py
# names
# still do decide
def hierarchical_beta(name, name_sigma, pr_mean, pr_sigma, len_L2):

    if not len_L2:  # not hierarchical
        Y = pm.Beta(name, alpha=pr_mean / pr_sigma, beta=1 / pr_sigma * (1 - pr_mean))
        X = None
    else:
        sigma_Y = pm.HalfCauchy(name_sigma + "_L2", beta=pr_sigma)
        X = pm.Beta(
            name + "_L1", alpha=pr_mean / pr_sigma, beta=1 / pr_sigma * (1 - pr_mean)
        )
        Y = pm.Beta(
            name + "_L2", alpha=X / sigma_Y, beta=1 / sigma_Y * (1 - X), shape=len_L2
        )

    return Y, X


# utility.py
def tt_lognormal(x, mu, sigma):
    distr = 1 / x * tt.exp(-((tt.log(x) - mu) ** 2) / (2 * sigma ** 2))
    return distr / (tt.sum(distr, axis=0) + 1e-5)