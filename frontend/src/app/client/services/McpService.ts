/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { MCPEnabledRequest } from '../models/MCPEnabledRequest';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class McpService {
    /**
     * Set Mcp Enabled
     * @param requestBody
     * @returns any Successful Response
     * @throws ApiError
     */
    public static setMcpEnabledMcpMcpEnabledPut(
        requestBody: MCPEnabledRequest,
    ): CancelablePromise<any> {
        return __request(OpenAPI, {
            method: 'PUT',
            url: '/mcp/mcp_enabled',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
