"""The maturity ramp (primary at 20/40/60/80/100 percent) keeps every step distinguishable in protanopia, deuteranopia and
tritanopia: the closest pair is at least 0.08 OKLab apart, for the library's tokens and the brand tokens, light and dark."""
import importlib.util
import pathlib

spec = importlib.util.spec_from_file_location('capability_ramp', pathlib.Path(__file__).resolve().parents[1] / 'scripts' / 'capability_ramp.py')
ramp = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ramp)


def test_closest_pair_meets_the_threshold_in_every_simulation():
    for key, sims in ramp.closest().items():
        assert set(sims) == {'normal', 'protanopia', 'deuteranopia', 'tritanopia'}
        for sim, (distance, a, b) in sims.items():
            assert distance >= 0.08, f'{key} {sim}: steps {a} and {b} are {distance:.4f} apart'


def test_the_page_ramp_classes_are_the_five_opacity_steps_of_primary():
    from flask_basecoat import capability
    text = (pathlib.Path(ramp.__file__).resolve().parents[1] / 'flask_basecoat/templates/basecoat/capability_map/_parts.html').read_text()
    for cls in ('bg-primary/20', 'bg-primary/38', 'bg-primary/56', 'bg-primary/76', "5: 'bg-primary'", "0: 'border-dashed'"):
        assert cls in text
    assert capability.steps({'maturity': 4, 'strategicImportance': 'critical', 'currentInvestment': 'none'}) == {'maturity': 4, 'importance': 5, 'investment': 0}
