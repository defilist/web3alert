import { IRouter } from '../../../../src/core/server';
import axios from 'axios';

export function defineAlertsRoute(router: IRouter) {
  router.get(
    {
      path: '/api/web3_soc/policies',
      validate: false,
    },
    async (context, request, response) => {
      try {
        const res= await axios.get('http://10.132.83.97:8880/api/v0/rules');
        return response.ok({
        	body: res.data,
					headers: {
						'Access-Control-Allow-Origin': 'http://localhost:5601',
					}
				});
      } catch (error) {
        // Handle error appropriately
        return response.customError({
					statusCode: error.response?.status || 500,
					body: error.message
				});
      }
    }
  );
}