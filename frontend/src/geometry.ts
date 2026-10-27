/** Bounds of SVG path data made of absolute M/L/Z commands. */
export function pathBounds(d: string): [number, number, number, number] {
  const nums = d.match(/-?\d+(\.\d+)?/g)?.map(Number) ?? [0, 0]
  let [minX, minY, maxX, maxY] = [Infinity, Infinity, -Infinity, -Infinity]
  for (let i = 0; i + 1 < nums.length; i += 2) {
    minX = Math.min(minX, nums[i])
    maxX = Math.max(maxX, nums[i])
    minY = Math.min(minY, nums[i + 1])
    maxY = Math.max(maxY, nums[i + 1])
  }
  return [minX, minY, maxX, maxY]
}
