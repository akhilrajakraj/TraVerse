import { useEffect, useRef } from "react";
import * as THREE from "three";

export default function Compass3D() {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;
    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(50, 1, 0.1, 100);
    const renderer = new THREE.WebGLRenderer({ alpha: true, antialias: true });
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setSize(container.clientWidth || 500, container.clientHeight || 500);
    container.appendChild(renderer.domElement);

    const group = new THREE.Group();
    const ringMaterial = new THREE.MeshPhongMaterial({ color: 0x12304a, shininess: 90, transparent: true, opacity: 0.92 });
    const orangeMaterial = new THREE.MeshPhongMaterial({ color: 0xf56b32, shininess: 100 });
    const darkMaterial = new THREE.MeshPhongMaterial({ color: 0x12304a, shininess: 100 });
    const ring = new THREE.Mesh(new THREE.TorusGeometry(2.15, 0.09, 18, 96), ringMaterial);
    const north = new THREE.Mesh(new THREE.ConeGeometry(0.46, 2.8, 4), orangeMaterial);
    north.position.y = 1.4;
    const south = new THREE.Mesh(new THREE.ConeGeometry(0.46, 2.8, 4), darkMaterial);
    south.position.y = -1.4;
    south.rotation.x = Math.PI;
    group.add(ring, north, south);
    scene.add(group);
    scene.add(new THREE.DirectionalLight(0xffffff, 1.2));
    const ambient = new THREE.AmbientLight(0xffffff, 0.65);
    scene.add(ambient);
    camera.position.z = 7.5;

    let pointerX = 0;
    let pointerY = 0;
    const onPointerMove = (event: PointerEvent) => {
      pointerX = (event.clientX / window.innerWidth) * 2 - 1;
      pointerY = -(event.clientY / window.innerHeight) * 2 + 1;
    };
    const onResize = () => {
      const width = container.clientWidth || 500;
      const height = container.clientHeight || 500;
      renderer.setSize(width, height);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    };
    window.addEventListener("pointermove", onPointerMove);
    window.addEventListener("resize", onResize);
    let frame = 0;
    const animate = () => {
      frame = requestAnimationFrame(animate);
      group.rotation.y += 0.004;
      group.rotation.x = pointerY * 0.25;
      group.rotation.z = -pointerX * 0.25;
      renderer.render(scene, camera);
    };
    animate();
    return () => {
      cancelAnimationFrame(frame);
      window.removeEventListener("pointermove", onPointerMove);
      window.removeEventListener("resize", onResize);
      [ring.geometry, north.geometry, south.geometry].forEach((geometry) => geometry.dispose());
      [ringMaterial, orangeMaterial, darkMaterial].forEach((material) => material.dispose());
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, []);

  return <div ref={containerRef} className="compass-canvas" />;
}