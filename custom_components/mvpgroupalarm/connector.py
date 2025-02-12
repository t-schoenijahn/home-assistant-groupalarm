"""Connector Class for GroupAlarm Data."""

from datetime import datetime
import logging
import json
import requests

from homeassistant.const import STATE_UNKNOWN, STATE_OFF, STATE_ON
from .const import DEFAULT_TIMEOUT, GROUPALARM_URL

_LOGGER = logging.getLogger(__name__)


class GroupAlarmData:
    """helper class for centrally querying the data from GroupAlarm."""

    def __init__(self, hass, api_key, only_own_alarms = True):
        """Initiate necessary data for the helper class."""
        self._hass = hass

        self.success = False
        self.latest_update = None

        self.alarms = None
        self.user = None
        self.organizations = None

        if api_key != "":
            self.api_key = api_key
        self.only_own_alarms = only_own_alarms != False

    async def async_update(self):
        """Asynchronous update for all GroupAlarm entities."""
        return await self._hass.async_add_executor_job(self._update)

    def _update(self):
        """Update for all GroupAlarm entities."""
        timestamp = datetime.now()

        if not self.api_key:
            _LOGGER.exception("No update possible")
        else:
            self.request_headers = {"Personal-Access-Token": self.api_key}
            try:
                status_alarms, self.alarms = self.request_alarms()
                status_user, self.user = self.request_user()
                status_organization, self.organizations = self.request_organizations()

                self.success = status_alarms == 200 and status_user == 200 and status_organization == 200
            except requests.exceptions.HTTPError as ex:
                _LOGGER.error("Error: %s", ex)
                self.success = False
            else:
                self.latest_update = timestamp
            _LOGGER.debug("Values updated at %s", self.latest_update)

    def request_alarms(self):
        if self.only_own_alarms:
            url = GROUPALARM_URL + "/alarms/alarmed"
        else:
            url = GROUPALARM_URL + "/alarms/user"
        _LOGGER.debug("Using alarm url: %s", url)
        alarms = requests.get(url=url, headers=self.request_headers, timeout=DEFAULT_TIMEOUT)
        _LOGGER.debug("Getting alarms returned: %s", alarms.content)
        return alarms.status_code, alarms.json()

    def request_user(self):
        response = requests.get(url=GROUPALARM_URL + "/user", headers=self.request_headers, timeout=DEFAULT_TIMEOUT)
        _LOGGER.debug("Getting user returned: %s", response.content)
        return response.status_code, response.json()
    
    def request_organizations(self):
        organizations = {}
        response = requests.get(url=GROUPALARM_URL + "/organizations/paginated", headers=self.request_headers, timeout=DEFAULT_TIMEOUT)
        _LOGGER.debug("Getting organizations returned: %s", response.content)
        for organization in response.json()["organizations"]:
            id = organization["id"]
            name = organization["name"]
            organizations[id] = name
        
        return response.status_code, organizations

    def get_user(self):
        """Return information about the user."""
        return {
            "id": self.user["id"],
            "email": self.user["email"],
            "name": self.user["name"],
            "surname": self.user["surname"],
        }

    def __get_last_alarm(self):
      alarmList = self.alarms["alarms"]
      if len(alarmList) > 0:
        return alarmList[0]

    def get_alarm_id(self):
       alarm = self.__get_last_alarm()
       if alarm:
        return alarm["id"]
       else:
         return None
       
    def get_alarm_organization(self):
       alarm = self.__get_last_alarm()
       if alarm:
        return self.get_organization_name_by_id(alarm["organizationID"])
       else:
        return None

    def get_alarm_message(self):
       alarm = self.__get_last_alarm()
       if alarm:
        return alarm["message"]
       else:
        return None

    def get_alarm_event(self):
       alarm = self.__get_last_alarm()
       if alarm:
          return alarm["event"]["name"]
       else:
          return None
    
    def get_alarm_start(self):
       alarm = self.__get_last_alarm()
       if alarm:
          return datetime.fromisoformat(alarm["startDate"])
       else:
          return None

    def get_alarm_end(self):
       alarm = self.__get_last_alarm()
       if alarm and "endDate" in alarm:
          return datetime.fromisoformat(alarm["endDate"])
       else:
          return None

    def get_alarm_feedback(self):
      alarm = self.__get_last_alarm()
      try:
        return self.get_user_feedback(alarm["feedback"])
      except UserNotAlarmedException:
        return None
       

    def get_alarm_useralarmed(self):
      alarm = self.__get_last_alarm()
      try:
        self.get_user_feedback(alarm["feedback"])
        return True
      except UserNotAlarmedException:
        return False

    def get_alarm_state(self):
        """Return informations of last alarm."""
        alarmList = self.alarms["alarms"]
        if len(alarmList) > 0:
            alarm = alarmList[0]
            if (datetime.fromisoformat(alarm["startDate"]) < datetime.now().astimezone()) and ( 
                (not "endDate" in alarm) or
                (datetime.fromisoformat(alarm["endDate"]) > datetime.now().astimezone())
                ):
                return STATE_ON
            else:
                return STATE_OFF
        else:
            return STATE_UNKNOWN

    def get_organization_name_by_id(self, organization):
        """Return the name from the given group id."""
        try:
            return str(self.organizations[organization])
        except KeyError:
            return None
        
    def get_user_feedback(self, alarmFeedback):
        ownId = self.get_user()["id"]
        for feedback in alarmFeedback:
            if feedback["userID"] == ownId:
                if feedback["state"] == "WAITING":
                    return None
                else:
                    return feedback["feedback"]
        raise UserNotAlarmedException()

    def set_state(self, state_id):
        """Set the state of the user to the given id."""
        payload = json.dumps({"Status": {"id": state_id}})
        headers = {"Content-Type": "application/json"}

        if not self.api_key:
            _LOGGER.exception("state can not be set. api-key is missing")
        else:
            headers = {"Content-Type": "application/json", "accesskey": self.api_key}
            try:
                response = requests.post(
                    headers=headers,
                    timeout=DEFAULT_TIMEOUT,
                    data=payload,
                )
                if response.status_code != 200:
                    _LOGGER.error("Error while setting the state")
            except requests.exceptions.HTTPError as ex:
                _LOGGER.error("Error: %s", ex)

class UserNotAlarmedException(Exception):
    pass