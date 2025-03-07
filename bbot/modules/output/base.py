import logging

from bbot.modules.base import BaseModule


class BaseOutputModule(BaseModule):
    accept_dupes = True
    _type = "output"
    emit_graph_trail = True
    scope_distance_modifier = None
    _stats_exclude = True

    def _filter_event(self, event, precheck_only=False):
        if type(event) == str:
            if event in ("FINISHED", "REPORT"):
                return True, ""
            else:
                return False, f'string value "{event}" is invalid'
        if event._omit:
            return False, "_omit is True"
        if not precheck_only:
            if event._force_output:
                return True, "_force_output is True"
            if event._internal:
                return False, "_internal is True"
        return True, ""

    @property
    def config(self):
        config = self.scan.config.get("output_modules", {}).get(self.name, {})
        if config is None:
            config = {}
        return config

    @property
    def log(self):
        if self._log is None:
            self._log = logging.getLogger(f"bbot.modules.output.{self.name}")
        return self._log
