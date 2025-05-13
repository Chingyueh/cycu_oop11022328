


# homework 2
class BusInfo:
    def __init__(self, bus_id):
        self.bus_id = bus_id

    def get_route_info_go(self):
        """
        回傳此巴士的路線資料 的所有車站 id (按照順序)
        另如  ['stop_id1' , 'stop_id2' , ...]
        """
        route_info = ['stop_id1', 'stop_id2']
        # Example data, replace with actual data retrieval logic
        return route_info

    def get_route_info_come(self):
        """
        回傳此巴士的路線資料 的所有車站 id (按照順序)
        另如  ['stop_id1' , 'stop_id2' , ...]
        """
        route_info = ['stop_id3', 'stop_id4']
        # Example data, replace with actual data retrieval logic
        return route_info

    def get_stop_name(self , stop_id):
        """
        Retrieve stop name and location information.
        :param stop_id: The ID of the bus stop.
        :return: A dictionary containing the stop name 

        """
        stop_name = "台北火車站"
        return stop_name

    def get_arrival_time_info(self, stop_id):
        """
        Retrieve arrival time (min 分鐘) for the bus.
        To be implemented.
        """
        arrival_time = 5
        return arrival_time
        


if __name__ == "__main__":


    bus = BusInfo("M25305")
    print(f"Bus ID: {bus.bus_id}")
    print(f"Route Info Go: {bus.get_route_info_go()}")
    print(f"Route Info Come: {bus.get_route_info_come()}")

    # get stop name of second stop of route_info_go
    route_info_go = bus.get_route_info_go()
    stop_id = route_info_go[1] if len(route_info_go) > 1 else None  
    if stop_id:
        stop_name = bus.get_stop_name(stop_id)
        print(f"Stop Name: {stop_name}")
    else:
        print("No stop ID available.")

    # get arrival time of second stop of route_info_go
    if stop_id:
        arrival_time = bus.get_arrival_time_info(stop_id)
        print(f"Arrival Time: {arrival_time} minutes")
    else:
        print("No stop ID available.")