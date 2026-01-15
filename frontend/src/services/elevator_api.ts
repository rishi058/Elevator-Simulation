import Api from "./api_interceptor";
import type { ElevatorStatus } from "../store/elevatorStore";

// Response type from backend /api/status
interface StatusResponse {
  total_floors: number;
  elevators: ElevatorStatus[];
}

class Elevator extends Api{
  
    async getStatus(): Promise<StatusResponse | null> {
        try {
            const response = await this.Api.get<StatusResponse>("/api/status");
            
            if (response.status >= 200 && response.status < 300) {
              return response.data;
            } else {
              throw new Error(`Error fetching status: ${response.status} - ${response.data}`);
            }

        } catch (e) {
            console.error(e);
            return null;
        }
    }

    async addRequest(floor: number, direction: 'U' | 'D') {
        try {
            const response = await this.Api.post("/api/request",{
                floor: floor,
                direction: direction,
            }); 

            if (response.status == 200) {
                return response.data;
            } else {
              console.error(response.data);
              return "";
            }
        } catch (e) {
            console.error(e instanceof Error ? e.message : String(e));
            return "";
        }
    }

    async addStop(elevator_id: number, stop: number) {
        try{
            const response = await this.Api.post("/api/stop", {
                elevator_id: elevator_id,
                floor: stop,
            }); 

            if(response.status == 200){
                return response.data;
            }else{
                console.error(response.data);
                return false;
            }
      } catch (e) {
        console.error(e instanceof Error ? e.message : String(e));
        return false;
      }
    }

    async initialize_building(total_floors: number, total_elevators: number) {
      try {
        const response = await this.Api.post("/api/building", {
            total_floors: total_floors,
            total_elevators: total_elevators
        }); 

        if(response.status == 200){
            return response.data;
        } else {
            console.error(response.data);
            return false;
        }
        } catch (e) {
            console.error(e instanceof Error ? e.message : String(e));
            return false;
        }
    }

}

export default Elevator;
