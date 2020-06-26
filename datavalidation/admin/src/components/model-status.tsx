import * as React from 'react';

import tick from '../icons/tick.svg';
import cross from '../icons/cross.svg';
import busy from '../icons/busy.svg';


export enum ModelStatus {
    PASSING = 0,
    FAILING = 1,
    EXCEPTION = 2,
    WARNING = 3,
}


export const modelStatusColour = (status: ModelStatus): string => {
    switch (status) {
        case ModelStatus.PASSING:
            return "#00b050";
        case ModelStatus.FAILING:
            return "#c00000";
        case ModelStatus.WARNING:
            return "#ffff00";
        case ModelStatus.EXCEPTION:
            return "#bcbcbc";
        default:
            return "#000000"
    }
}


export const ModelStatusIndicator: React.FC<{status: ModelStatus}> = ({
    status
}) => {
    let icon: string;
    switch (status) {
        case ModelStatus.PASSING:
            icon = tick;
            break;
        case ModelStatus.FAILING:
            icon = cross;
            break;
        default:
            icon = busy;
    }

    return (
        <img src={icon} className="icon" alt="" />
    )
}


