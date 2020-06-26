import * as React from 'react';
import {ModelStatus} from "./model-status";


export interface MethodRowInterface {
    appLabel: string,
    modelName: string,
    status: ModelStatus,
    methods: any[],
}