import * as React from 'react';
import {FC, SVGProps} from 'react';

import {Status} from "../data/enums";
import {ReactComponent as Tick} from '../icons/tick.svg';
import {ReactComponent as Cross} from '../icons/cross.svg';
import {ReactComponent as Exclamation} from '../icons/exclamation.svg';


const getIcon = (status: Status): FC<SVGProps<SVGSVGElement>> => {
    switch (status) {
        case Status.UNINITIALIZED:
        case Status.PASSING:
            return Tick;
        case Status.FAILING:
            return Cross;
        case Status.EXCEPTION:
        case Status.WARNING:
            return Exclamation;
    }
}


export const getStatusColour = (status: Status, onDark: boolean = false): string => {
    switch (status) {
        case Status.PASSING:
            return onDark ? "#00fe74" : "#009744";
        case Status.FAILING:
            return onDark ? "#500000" : "#8e0000";
        case Status.UNINITIALIZED:
        case Status.EXCEPTION:
            return onDark ? "#c6d2cd" : "#7e8482";
        case Status.WARNING:
            return onDark ? "#fff409" : "#847e05";
    }
}


export const getStatusContrastColour = (status: Status, onDark: boolean = false): string => {
    switch (status) {
        case Status.UNINITIALIZED:
        case Status.PASSING:
        case Status.EXCEPTION:
        case Status.WARNING:
            return onDark ? "#696969" : "#fff";
        case Status.FAILING:
            return "#fff";
    }
}


interface IStatusIndicator {
    status: Status,
    onDark: boolean
}


export const StatusIcon: FC<IStatusIndicator> = ({
    status, onDark
}) => {
    const icon = getIcon(status);
    const fill = getStatusColour(status, onDark);
    const stroke = getStatusContrastColour(status, onDark);
    return React.createElement(icon, {className: "icon", fill, stroke});
}


export const StatusIndicator: FC<IStatusIndicator> = ({
    status, onDark
}) => {
    return (
        <div className="vertical-align">
            <StatusIcon status={status} onDark={onDark}/>
            <span style={{color: getStatusColour(status, onDark)}}>
                {Status[status]}
            </span>
        </div>
    );
}
