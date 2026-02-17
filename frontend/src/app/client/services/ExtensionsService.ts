/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ExtensionTool } from '../models/ExtensionTool';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class ExtensionsService {
    /**
     * Get Connected Extension Tools
     * Returns a list of all currently registered and connected extension tools.
     * @returns ExtensionTool Successful Response
     * @throws ApiError
     */
    public static getConnectedExtensionToolsExtensionsConnectedToolsGet(): CancelablePromise<Array<ExtensionTool>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/extensions/connected_tools',
        });
    }
}
