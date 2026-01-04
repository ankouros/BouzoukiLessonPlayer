from metronome.metronome import CLICK, ACCENT, SOFT_CLICK, SOFT_ACCENT


def _resolve_wave_objects_for_profile(profile: str):
    """Pure helper mirroring MetronomeUI._resolve_wave_objects logic minus WAV/Qt."""
    if profile == "soft":
        return SOFT_CLICK, SOFT_ACCENT
    if profile == "wood":
        from metronome.metronome import WOOD_CLICK, WOOD_ACCENT

        return WOOD_CLICK, WOOD_ACCENT
    if profile == "clave":
        from metronome.metronome import CLAVE_CLICK, CLAVE_ACCENT

        return CLAVE_CLICK, CLAVE_ACCENT
    if profile == "metal":
        from metronome.metronome import METAL_CLICK, METAL_ACCENT

        return METAL_CLICK, METAL_ACCENT
    return CLICK, ACCENT


def test_resolve_wave_objects_uses_default_clicks_for_classic_profile():
    w_r, w_a = _resolve_wave_objects_for_profile("classic")
    assert w_r is CLICK
    assert w_a is ACCENT


def test_resolve_wave_objects_uses_soft_clicks_for_soft_profile():
    w_r, w_a = _resolve_wave_objects_for_profile("soft")
    assert w_r is SOFT_CLICK
    assert w_a is SOFT_ACCENT


def test_resolve_wave_objects_for_clave_and_metal_profiles():
    w_r_clave, w_a_clave = _resolve_wave_objects_for_profile("clave")
    w_r_metal, w_a_metal = _resolve_wave_objects_for_profile("metal")

    # They should resolve to distinct, non-default pairs
    assert (w_r_clave, w_a_clave) != (CLICK, ACCENT)
    assert (w_r_metal, w_a_metal) != (CLICK, ACCENT)
