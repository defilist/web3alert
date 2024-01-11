import { IRouter } from '../../../../src/core/server';
import axios from 'axios';

export function defineAlertsRoute(router: IRouter) {
  router.get(
    {
      path: '/api/web3_soc/alerts',
      validate: false,
    },
    async (context, request, response) => {
      try {
        const { data } = await axios.get('http://10.132.83.97:8880/api/v0/alerts/59c842cc-1d7d-42dc-86fa-e6b3d889532a');
        return response.ok({
        	body: data,
					headers: {
						'Access-Control-Allow-Origin': 'http://localhost:5601',
					}
				});
      } catch (error) {
        // Handle error appropriately
        return response.internalError({ body: error });
      }
    }
  );
}