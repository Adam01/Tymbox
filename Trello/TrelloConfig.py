import json
import os

from requests_oauthlib import OAuth1Session

from Utils.LogHelper import LogHelper


class TrelloConfig(LogHelper):
    def __init__(self):
        LogHelper.__init__(self, "TrelloConfig")

        self.data = dict(api_key="",
                        api_secret="",
                        token="",
                        token_secret="")

        self.resource_owner_key = None
        self.resource_owner_secret = None

    def request_oauth(self, key, secret):
        request_token_url = 'https://trello.com/1/OAuthGetRequestToken'
        authorize_url = 'https://trello.com/1/OAuthAuthorizeToken'

        expiration = "30days"
        scope = 'read,write'
        self.data["api_key"] = key
        self.data["api_secret"] = secret
        name = 'Tymbox'

        self.log_debug("Request",
                       expiration=expiration,
                       scope=scope,
                       trello_key=self.data["api_key"],
                       trello_secret=self.data["api_secret"],
                       name=name,
                       request_token_url=request_token_url,
                       authorize_url=authorize_url)

        session = OAuth1Session(client_key=self.data["api_key"], client_secret=self.data["api_secret"])
        response = session.fetch_request_token(request_token_url)
        self.resource_owner_key, self.resource_owner_secret = response.get('oauth_token'), response.get('oauth_token_secret')

        self.log_debug("Request token",
                       oauth_token=self.resource_owner_key,
                       oauth_token_secret=self.resource_owner_secret)

        auth_url = "{authorize_url}?oauth_token={oauth_token}&scope={scope}&expiration={expiration}&name={name}".format(
                        authorize_url=authorize_url,
                        oauth_token=self.resource_owner_key,
                        expiration=expiration,
                        scope=scope,
                        name=name
                    )

        return auth_url

    def complete_oauth(self, oauth_verifier):
        access_token_url = 'https://trello.com/1/OAuthGetAccessToken'

        self.log_debug("complete oauth",
                       trello_key=self.data["api_key"],
                       trello_secret=self.data["api_secret"],
                       resource_owner_key=self.resource_owner_key,
                       resource_owner_secret=self.resource_owner_secret,
                       oauth_verifier=oauth_verifier)

        session = OAuth1Session(client_key=self.data["api_key"], client_secret=self.data["api_secret"],
                                resource_owner_key=self.resource_owner_key, resource_owner_secret=self.resource_owner_secret,
                                verifier=oauth_verifier)
        access_token = session.fetch_access_token(access_token_url)

        self.data["token"] = access_token["oauth_token"]
        self.data["token_secret"] = access_token["oauth_token_secret"]

        return len(self.data["token"]) > 0 and len(self.data["token_secret"]) > 0

    def load_from_file(self, file_name) -> bool:
        if file_name is not None and len(file_name):
            try:
                fp = open(file_name)
                data = json.load(fp)
                if data is not None:
                    self.data = data
                    return True
            except:
                pass
        return False

    def save_to_file(self, file_name):
        if file_name is not None and len(file_name):
            try:
                dir_name = os.path.dirname(file_name)
                if not os.path.exists(dir_name):
                    os.makedirs(dir_name)
                fp = open(file_name, 'w')
                json.dump(self.data, fp)
                fp.close()
                return True
            except:
                pass
        return False

    @property
    def client_config(self) -> dict:
        return self.data
