---
title: "Component separation and foreground modelling."
image: "images/foregrounds_sed.png"
image_alt: "Frequency dependence of the CMB and foregrounds. Top: temperature at small scales (ACT DR6 foreground model). Bottom: B-mode polarisation at large scales, with dust and synchrotron levels from BICEP/Keck."
caption: "CMB and foregrounds vs frequency. Top: ACT DR6 model. Bottom: [BICEP/Keck](https://arxiv.org/abs/2110.00483) dust and synchrotron."
weight: 1
---

The CMB is not alone in the microwave sky. Galactic dust and synchrotron, the cosmic infrared background, radio sources and the Sunyaev–Zel'dovich effects all emit at millimetre wavelengths.
Their frequency dependence differs from that of the CMB, which makes it possible to model them or to separate them from it. Doing this accurately is essential for unbiased cosmology.
I work on this problem from small-scale power spectra to the search for primordial B-modes:

- **Foreground modelling for ACT.** I described and validated the parametric foreground model of the ACT DR6 multi-frequency power spectra, testing it against Planck and SPT data, model extensions and realistic non-Gaussian sky simulations. In all cases, ΛCDM and ΛCDM+N<sub>eff</sub> parameters shift by less than 0.5σ. The kinematic Sunyaev–Zel'dovich power also gives a limit on the duration of reionization ([Beringue, Surrao et al. 2025](https://arxiv.org/abs/2506.06274)).
- <a href="https://github.com/CMBSciPol/Megatop"><img class="inline-logo" src="/images/megatop_logo.png" alt="MEGATOP"></a> **for the Simons Observatory.** I co-lead the development of [MEGATOP](https://github.com/CMBSciPol/Megatop), a pipeline for the SO Small Aperture Telescopes that goes from frequency maps to *r* through map-based parametric component separation.
- **SMICA for B-modes from space.** We extended the semi-blind Spectral Matching ICA method to handle spatially varying foregrounds, by adding effective components and running it on separate sky regions, combined with foreground-template marginalisation in the likelihood. On LiteBIRD-like simulations this recovers an effectively unbiased tensor-to-scalar ratio *r*, with uncertainties of order 10<sup>−3</sup> ([Tran et al. 2026](https://arxiv.org/abs/2610.02301)).
