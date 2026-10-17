"""payment-guard: which payment platform can you open, and will your website pass its review."""
from pathlib import Path

__version__ = "0.3.1"
UA = f"Mozilla/5.0 (compatible; payment-guard/{__version__}; +https://github.com/zhuyansen/payment-guard)"
DATA = Path(__file__).parent / "data"
