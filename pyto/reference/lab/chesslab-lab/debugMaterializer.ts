/** A text projection of an already materialized value. No execution or I/O. */
export function DebugMaterializer<T>(value:T, view:(value:T)=>string):string {
 return view(value);
}
