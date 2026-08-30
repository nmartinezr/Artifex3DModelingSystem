import { useEffect, useRef, useState } from 'react';
import {
  Box3,
  Color,
  DirectionalLight,
  HemisphereLight,
  PerspectiveCamera,
  Scene,
  Sphere,
  SRGBColorSpace,
  Vector3,
  WebGLRenderer,
} from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';

export type ViewerStatus = 'empty' | 'loading' | 'ready' | 'error';

interface ModelViewerProps {
  assetUrl?: string;
}

export function ModelViewer({ assetUrl }: ModelViewerProps) {
  const hostRef = useRef<HTMLDivElement>(null);
  const [status, setStatus] = useState<ViewerStatus>(assetUrl ? 'loading' : 'empty');
  const [message, setMessage] = useState('Enter an ARTIFEX asset ID to inspect a generated model.');

  useEffect(() => {
    const host = hostRef.current;
    if (!host || !assetUrl) {
      setStatus('empty');
      setMessage('Enter an ARTIFEX asset ID to inspect a generated model.');
      return;
    }

    setStatus('loading');
    setMessage('Loading generated model…');

    let disposed = false;
    let frameId = 0;
    let renderer: WebGLRenderer;

    try {
      renderer = new WebGLRenderer({ antialias: true, alpha: false, powerPreference: 'high-performance' });
    } catch {
      setStatus('error');
      setMessage('WebGL is not available in this browser.');
      return;
    }

    renderer.outputColorSpace = SRGBColorSpace;
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    renderer.setClearColor(new Color(0x15171d), 1);
    host.replaceChildren(renderer.domElement);

    const scene = new Scene();
    scene.up.set(0, 0, 1);

    const camera = new PerspectiveCamera(45, 1, 0.01, 100000);
    camera.up.set(0, 0, 1);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.screenSpacePanning = true;

    const hemisphere = new HemisphereLight(0xffffff, 0x303540, 2.2);
    scene.add(hemisphere);
    const key = new DirectionalLight(0xffffff, 3.0);
    key.position.set(2, -3, 4);
    scene.add(key);
    const fill = new DirectionalLight(0xffffff, 1.2);
    fill.position.set(-3, 2, 1.5);
    scene.add(fill);

    const resize = () => {
      const width = Math.max(host.clientWidth, 1);
      const height = Math.max(host.clientHeight, 1);
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    };

    const resizeObserver = new ResizeObserver(resize);
    resizeObserver.observe(host);
    resize();

    const renderFrame = () => {
      controls.update();
      renderer.render(scene, camera);
      frameId = window.requestAnimationFrame(renderFrame);
    };
    renderFrame();

    const loader = new GLTFLoader();
    loader.load(
      assetUrl,
      (gltf) => {
        if (disposed) return;
        gltf.scene.traverse((object) => {
          object.frustumCulled = true;
        });
        scene.add(gltf.scene);

        const box = new Box3().setFromObject(gltf.scene);
        if (box.isEmpty()) {
          setStatus('error');
          setMessage('The generated asset does not contain visible geometry.');
          return;
        }

        const sphere = box.getBoundingSphere(new Sphere());
        const center = sphere.center;
        const radius = Math.max(sphere.radius, 0.001);
        controls.target.copy(center);

        const viewDirection = new Vector3(1.25, -1.6, 1.0).normalize();
        const distance = radius / Math.sin((camera.fov * Math.PI) / 360) * 1.15;
        camera.position.copy(center).addScaledVector(viewDirection, distance);
        camera.near = Math.max(distance / 10000, 0.001);
        camera.far = Math.max(distance * 100, radius * 1000);
        camera.updateProjectionMatrix();
        controls.update();

        setStatus('ready');
        setMessage('Generated model ready. Drag to orbit, right-drag to pan, and scroll to zoom.');
      },
      undefined,
      () => {
        if (!disposed) {
          setStatus('error');
          setMessage('The model could not be loaded. Verify the ARTIFEX asset ID and GLB format.');
        }
      },
    );

    return () => {
      disposed = true;
      window.cancelAnimationFrame(frameId);
      resizeObserver.disconnect();
      controls.dispose();
      scene.traverse((object) => {
        const mesh = object as unknown as {
          geometry?: { dispose: () => void };
          material?: { dispose: () => void } | Array<{ dispose: () => void }>;
        };
        mesh.geometry?.dispose();
        if (Array.isArray(mesh.material)) {
          mesh.material.forEach((material) => material.dispose());
        } else {
          mesh.material?.dispose();
        }
      });
      renderer.dispose();
      renderer.domElement.remove();
    };
  }, [assetUrl]);

  return (
    <section className="viewer-panel" data-qa-id="generated-model-viewer">
      <div ref={hostRef} className="viewer-canvas" data-qa-id="generated-model-viewer-canvas" />
      <p className={`viewer-status viewer-status--${status}`} data-qa-id="generated-model-viewer-status">
        {message}
      </p>
    </section>
  );
}
