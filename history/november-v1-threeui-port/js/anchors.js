// Stable attachment contract, in metres, frozen against aerix-v01.glb / master v30.
// Materials and child geometry may change without changing framing. Preserve named
// roots, root transforms, scale and these authored targets. Never fit cameras to bounds.
export const MODEL_OFFSET = [0.000002171623, -0.068499998597, -0.032954218449];
export const ROOTS = {
  battery: "BATTERY_ROOT",
  thermal: "THERMAL_ROOT",
  computer: "FLIGHT_COMPUTER_ROOT",
  tray: "INTERNAL_SUPPORT_ROOT",
  optics: "CAMERA_GIMBAL_ROOT",
  chassis: "INTERIOR_CHASSIS_ROOT",
};
export const ANCHORS = {
  whole: { root: null, point: [0, 0, 0] },
  architecture: { root: null, point: [0, 0.12, 0] },
  battery: { root: "BATTERY_ROOT", point: [0, 0.139, -0.002145] },
  thermal: { root: "THERMAL_ROOT", point: [0, 0.085, -0.002] },
  computer: { root: "FLIGHT_COMPUTER_ROOT", point: [0, 0.075, -0.000746] },
  tray: { root: "INTERNAL_SUPPORT_ROOT", point: [0, 0.064, -0.003] },
  optics: { root: "CAMERA_GIMBAL_ROOT", point: [0, 0.038, 0.204] },
  lens: { root: "CAMERA_GIMBAL_ROOT", point: [0, 0.038, 0.18475] },
};
export const ROTOR_RADIUS = 0.1;
export const PLATFORM_TOP = -0.0564;
