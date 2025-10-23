import os
from traitlets.config import Configurable
from traitlets import Unicode

class MaapServerConfig(Configurable):
    """Configuration class for MAAP Jupyter Server Extension."""
    
    maap_api_url = Unicode(
        help="The MAAP API base URL, configurable via environment variable MAAP_API_URL",
        default_value=os.environ.get("MAAP_API_URL", "")
    ).tag(config=True)
