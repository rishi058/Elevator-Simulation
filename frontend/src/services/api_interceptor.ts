import axios from "axios";
import { showErrorToast, showToast } from "../utils/toast";

class Api {
    Api;
    baseURL = "http://localhost:8000";

    constructor() {
        this.Api = axios.create({
            baseURL : this.baseURL,
        });

        this.Api.interceptors.request.use((config) => {
            return config;
        }, (error) => {
            showErrorToast(error.message)
            console.error('Error:', error.message);
            return Promise.reject(error);
        });

        this.Api.interceptors.response.use((response) => {
            if(response.data.message){
                showToast(response.data.message);
                console.log('Message:', response.data.message);
            }
            return response;
        }, (error) => {
            showErrorToast(`Server Error: ${error.message}`);
            console.error('Server Error:', error.message);
            return Promise.reject(error);
        });
    }

}

export default Api;