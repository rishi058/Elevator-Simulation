import Api from "./api_interceptor";

class Elevator extends Api{
  
    async getStatus(){
        try {
            const response = await this.Api.get("/api/status");
            
            if (response.status >= 200 && response.status < 300) {
              return response.data;
            } else {
              throw new Error(`Error fetching status: ${response.status} - ${response.data}`);
            }

        } catch (e) {
            console.error(e);
            throw e;
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

    async addStop(stop: number) {
        try{
            const response = await this.Api.post("/api/stop", {
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

    async setFloors(floors: number) {
      try {
        const response = await this.Api.post("/api/total_floors", {
            total_floors: floors,
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
