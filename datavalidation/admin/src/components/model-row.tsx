import * as React from 'react';

import { ModelStatus, ModelStatusIndicator, modelStatusColour } from './model-status';


export interface ModelRowInterface {
    appLabel: string,
    modelName: string,
    status: ModelStatus,
    methods: any[],
}


/**
 * A row for each model displaying the data validation status
 */
export const ModelRow: React.FC<ModelRowInterface> = ({
     appLabel,
     modelName,
     status
}) => {
    return (
        <tr style={rowStyle}>
            <td> {appLabel} </td>
            <td> {modelName} </td>
            <td>
                <div className="vertical-align">
                    <ModelStatusIndicator status={status}/>
                    <span style={{color: modelStatusColour(status)}}>
                        {ModelStatus[status]}
                    </span>
                </div>
            </td>
        </tr>
    )
}


/**
 * the widths of the columns of the table
 */
export const ModelRowColgroup: React.FC<void> = () =>
    <colgroup>
        <col span={1} style={{width: "10%"}}  />
        <col span={1} style={{width: "20%"}} />
        <col span={1} />
    </colgroup>
;


const rowStyle: React.CSSProperties = {
    padding: '10px',
    background: '#ebebeb',
    fontWeight: 600,
    fontSize: '14pt',
    color: '#000000',
};




export default ModelRow;