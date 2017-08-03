class TrelloConfig(object):

    @property
    def api_key(self):
        return ""

    @property
    def api_secret(self):
        return ""

    @property
    def token(self):
        return ""

    @property
    def token_secret(self):
        return ""

    @property
    def client_config(self) -> dict:
        return dict(api_key=self.api_key,
                    api_secret=self.api_secret,
                    token=self.token,
                    token_secret=self.token_secret)
