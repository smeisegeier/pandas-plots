"""Internal helper to make kaleido's Chrome dependency work out of the box.

kaleido>=1 no longer bundles Chromium; it needs a Chrome binary that must be
downloaded once via `kaleido.get_chrome_sync()`. This is invisible on macOS/Linux
dev machines that happen to already have Chrome installed, but fails on a bare
Windows machine with a `ChromeNotFoundError` that gives users no obvious next step.
"""

_kaleido_chrome_checked = False


def _ensure_kaleido_chrome(verbose: bool = True) -> None:
    """
    Make sure kaleido can find a Chrome binary, downloading one if needed.

    Probes with a real (trivial) static render, since that's the same code path
    kaleido itself uses to look for Chrome - avoids depending on kaleido/choreographer
    private internals. Runs at most once per process.
    """
    global _kaleido_chrome_checked
    if _kaleido_chrome_checked:
        return
    _kaleido_chrome_checked = True

    try:
        import plotly.graph_objects as go

        go.Figure().to_image(format="svg")
        return
    except Exception:
        pass

    if verbose:
        try:
            answer = input(
                "pandas_plots: kaleido needs Chrome for static image export "
                "(one-time download, ~150 MB). Download now? [y/N] "
            ).strip().lower()
        except EOFError:
            answer = ""
        if answer != "y":
            print(
                "pandas_plots: skipped Chrome download. Static image export will fail "
                "until Chrome is available - rerun and confirm, install Chrome manually, "
                "or set BROWSER_PATH to an existing Chrome/Chromium binary."
            )
            return

    try:
        import kaleido

        kaleido.get_chrome_sync()
    except Exception as e:
        if verbose:
            print(
                f"pandas_plots: automatic Chrome download failed ({e}).\n"
                "Install Chrome, run `kaleido_get_chrome` manually, or set the "
                "BROWSER_PATH environment variable to an existing Chrome/Chromium binary."
            )
