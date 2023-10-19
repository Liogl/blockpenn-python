import requests, secrets, json

class Kasa(object):
    def __init__(self):
        self.api_url = "https://wap.tplinkcloud.com"
        self.devices = None
        self.kasa_token = None
        
        
    def create_random_uuid(self):
        uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'
        uuid = list(uuid)

        uuid_sec = secrets.token_hex(36)

        for uuid_index,uuid_char in enumerate(uuid):
            r = uuid_sec[uuid_index]
            d = int(r,16) & 0x3 | 0x8
            if (uuid_char == "x"):
                uuid[uuid_index] = r
            elif (uuid_char == "y"):
                uuid[uuid_index] = format(d,'01x')

        uuid = "".join(uuid)
        return uuid

    def set_auth_token(self, uuid, username, password):
        auth_obj = {
            "method": "login", 
            "params": {
                "appType": "Kasa_Android",
                "cloudUserName": username,
                "cloudPassword": password,
                "terminalUUID": uuid,
            }
        }

        response = requests.post(self.api_url+"/", json=auth_obj)
        kasa_token = response.json()["result"]["token"]
        self.kasa_token = kasa_token
        return response.status_code

    def get_set_dev_list(self):
        dev_obj = {"method": "getDeviceList"}
        response = requests.post(self.api_url+"?token="+self.kasa_token, json=dev_obj)
        self.devices = response.json()["result"]["deviceList"]
        return response.status_code, response.json()["error_code"], response.json()["result"]["deviceList"]

    def set_dev_state(self, sel_device_id, sel_device_state):
        set_obj = {
            "method": "passthrough", "params": {
                "deviceId": sel_device_id,
                "requestData": "{\"system\":{\"set_relay_state\":{\"state\":" + str(sel_device_state) + "}}}"
            }
        }
        response = requests.post(self.api_url+"?token="+self.kasa_token, json=set_obj)
        return response.status_code, response.json()["error_code"]

    def set_dev_state_emeter(self, sel_device_id):
        set_obj = {
            "method": "passthrough", "params": {
                "deviceId": sel_device_id,
                "requestData": "{\"system\":{\"get_sysinfo\":null},\"emeter\":{\"get_realtime\":null}}"
            }
        }
        response = requests.post(self.api_url+"?token="+self.kasa_token, json=set_obj)
        return response.status_code, response.json()["error_code"], response.json()

    def handle_devices(self, n=1):
        responses = []
        for device in self.devices[:n]:
            device_id = device["deviceId"]
            device_state = 1
            self.set_dev_state(device_id, device_state)
            responses.append(self.set_dev_state_emeter(device_id))
        return responses
    
    def get_power_energy_data(self):
        responses = {}
        for i, device in enumerate(self.devices):
            device_id = device["deviceId"]
            response = self.set_dev_state_emeter(device_id)[2]
            dev_ma = json.loads(response['result']['responseData'])['emeter']['get_realtime']['current_ma']
            dev_mv = json.loads(response['result']['responseData'])['emeter']['get_realtime']['voltage_mv']
            dev_mw = json.loads(response['result']['responseData'])['emeter']['get_realtime']['power_mw']
            dev_wh = json.loads(response['result']['responseData'])['emeter']['get_realtime']['total_wh']
            device_name = f"Device {i+1}"
            device_data = {
                device_name+": Current_Reading":dev_ma/1000,
                device_name+": Voltage_Reading":dev_mv/1000,
                device_name+": Power_Reading":dev_mw/1000,
                device_name+": Energy_Reading":dev_wh/1000,
            }
            responses[device_name] = device_data
        return responses