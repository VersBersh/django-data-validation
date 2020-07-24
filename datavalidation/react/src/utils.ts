

/** remove leading '/' from a string */
function trimLeadingSlash(str: string): string {
    return str.replace(/^\/+/, '');
}


/** remove trailing '/' from a string */
function trimTrailingSlash(str: string): string {
    return str.replace(/\/+$/, '');
}


type NonEmptyArray<T> = [T, ...T[]];


/** join together a list of non-relative urls */
export function urlJoin(base: string, ...paths: NonEmptyArray<string>): string {
    base = trimTrailingSlash(base);
    const end = trimLeadingSlash(paths.pop() as string);
    const middle = paths.map(trimLeadingSlash).map(trimTrailingSlash);
    return [base, ...middle, end].join("/");
}


/** return a new Date from a string */
export function parseDate(dateStr: string): Date {
    return new Date(Date.parse(dateStr));
}


/** pad a string to a fixed length */
function leftPad(value: string, len: number, fill: string = "0") {
    console.assert(fill.length === 1);
    const padLen = len - value.length;
    if (padLen < 0) {
        throw Error("value longer than fixed width")
    }
    return fill.repeat(padLen) + value;
}


const monthNames: {[index: number]: string} = {
    0: "Jan", 1: "Feb", 2: "Mar", 3: "Apr", 4: "May", 5: "Jun",
    6: "Jul", 7: "Aug", 8: "Sep", 9: "Oct", 10: "Nov", 11: "Dec",
};


/** format a date as a string */
export function formatDate(date: Date, formatStr: string): string {

    const formats: {[token: string]: () => string} = {
        "%Y": () => date.getFullYear().toString(),
        "%y": () => leftPad(date.getFullYear().toString().slice(2), 2),
        "%mm": () => monthNames[date.getMonth()],
        "%m": () => leftPad(date.getMonth().toString(),2),
        "%d": () => leftPad(date.getDate().toString(),2),
        "%H": () => leftPad(date.getHours().toString(),2),
        "%M": () => leftPad(date.getMinutes().toString(),2),
        "%S": () => leftPad(date.getSeconds().toString(),2),
    }

    Object.entries(formats).forEach(([token, callback]) => {
        formatStr = formatStr.replace(new RegExp(token, "g"), callback);
    });

    return formatStr;
}


/** format number of seconds as hh:mm:ss */
export function formatSeconds(seconds: number | null): string {
    if (seconds === null) {
        return "N/A"
    }
    let hrs = leftPad(Math.floor(seconds / 3600).toString(), 2);
    let rem = seconds % 3600;
    let min = leftPad(Math.floor(rem / 60).toString(), 2);
    let sec = leftPad((rem % 60).toFixed(1), 4)
    return `${hrs}:${min}:${sec}s`;
}


/** implementation of pythons collections.defaultdict */
export class DefaultDict<T extends string | number, U> extends Map<T, U> {
    defaultFactory: () => U;

    constructor(defaultFactory: () => U) {
        super();
        this.defaultFactory = defaultFactory;
    }

    get(key: T): U {
        if (this.has(key)) {
            return super.get(key) as U;
        } else {
            const value = this.defaultFactory();
            this.set(key, value);
            return value;
        }
    }
}
