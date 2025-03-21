############################################################
#                                                          #
#                                                          #
#    [-] Processing BuiltWith Domains Output               #
#                                                          #
#    [-] 2022.08.19                                        #
#          V05                                             #
#          Black Lantern Security (BLSOPS)                 #
#                                                          #
#                                                          #
############################################################

from .shodan_dns import shodan_dns


class builtwith(shodan_dns):

    watched_events = ["DNS_NAME"]
    produced_events = ["DNS_NAME"]
    flags = ["affiliates", "subdomain-enum", "passive", "safe"]
    meta = {"description": "Query Builtwith.com for subdomains", "auth_required": True}
    options = {"api_key": "", "redirects": True}
    options_desc = {"api_key": "Builtwith API key", "redirects": "Also look up inbound and outbound redirects"}
    base_url = "https://api.builtwith.com"

    def ping(self):
        # builtwith does not have a ping feature, so we skip it to save API credits
        return

    def handle_event(self, event):
        query = self.make_query(event)
        # domains
        subdomains = self.query(query, parse_fn=self.parse_domains, request_fn=self.request_domains)
        if subdomains:
            for s in subdomains:
                if s != event:
                    self.emit_event(s, "DNS_NAME", source=event)
        # redirects
        if self.config.get("redirects", True):
            redirects = self.query(query, parse_fn=self.parse_redirects, request_fn=self.request_redirects)
            if redirects:
                for r in redirects:
                    if r != event:
                        self.emit_event(r, "DNS_NAME", source=event, tags=["affiliate"])

    def request_domains(self, query):
        url = f"{self.base_url}/v20/api.json?KEY={self.api_key}&LOOKUP={query}&NOMETA=yes&NOATTR=yes&HIDETEXT=yes&HIDEDL=yes"
        return self.helpers.request(url)

    def request_redirects(self, query):
        url = f"{self.base_url}/redirect1/api.json?KEY={self.api_key}&LOOKUP={query}"
        return self.helpers.request(url)

    def parse_domains(self, r, query):
        """
        This method yields subdomains.
        Each subdomain is an "FQDN" that was reported in the "Detailed Technology Profile" page on builtwith.com

        Parameters
        ----------
        r (requests Response): The raw requests response from the API
        query (string): The query used against the API
        """
        json = r.json()
        if json:
            for result in json.get("Results", []):
                for chunk in result.get("Result", {}).get("Paths", []):
                    domain = chunk.get("Domain", "")
                    subdomain = chunk.get("SubDomain", "")
                    if domain:
                        if subdomain:
                            domain = f"{subdomain}.{domain}"
                        yield domain
            else:
                error = json.get("Errors", [{}])[0].get("Message", "Unknown Error")
                if error:
                    self.verbose(f"No results for {query}: {error}")

    def parse_redirects(self, r, query):
        """
        This method creates a set.
        Each entry in the set is either an Inbound or Outbound Redirect reported in the "Redirect Profile" page on builtwith.com

        Parameters
        ----------
        r (requests Response): The raw requests response from the API
        query (string): The query used against the API

        Returns
        -------
        results (set)
        """
        results = set()
        json = r.json()
        if json:
            inbound = json.get("Inbound", [])
            outbound = json.get("Outbound", [])
            if inbound:
                for i in inbound:
                    domain = i.get("Domain", "")
                    if domain:
                        results.add(domain)
            if outbound:
                for o in outbound:
                    domain = o.get("Domain", "")
                    if domain:
                        results.add(domain)
        if not results:
            error = json.get("error", "")
            if error:
                self.warning(f"No results for {query}: {error}")
        return results
