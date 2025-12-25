/* generated using openapi-typescript-codegen -- do not edit */
/* istanbul ignore file */
/* tslint:disable */
/* eslint-disable */
import type { ChunkPreviewRequest } from '../models/ChunkPreviewRequest';
import type { ChunkPreviewResponse } from '../models/ChunkPreviewResponse';
import type { File } from '../models/File';
import type { CancelablePromise } from '../core/CancelablePromise';
import { OpenAPI } from '../core/OpenAPI';
import { request as __request } from '../core/request';
export class FilesService {
    /**
     * Read Files
     * @param collectionId
     * @returns File Successful Response
     * @throws ApiError
     */
    public static readFilesFilesCollectionIdGet(
        collectionId: string,
    ): CancelablePromise<Array<File>> {
        return __request(OpenAPI, {
            method: 'GET',
            url: '/files/{collection_id}',
            path: {
                'collection_id': collectionId,
            },
            errors: {
                422: `Validation Error`,
            },
        });
    }
    /**
     * Get Chunk Preview
     * @param requestBody
     * @returns ChunkPreviewResponse Successful Response
     * @throws ApiError
     */
    public static getChunkPreviewFilesContentPost(
        requestBody: ChunkPreviewRequest,
    ): CancelablePromise<ChunkPreviewResponse> {
        return __request(OpenAPI, {
            method: 'POST',
            url: '/files/content',
            body: requestBody,
            mediaType: 'application/json',
            errors: {
                422: `Validation Error`,
            },
        });
    }
}
