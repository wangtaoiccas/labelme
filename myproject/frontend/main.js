/* global fetch */

const canvas = document.getElementById('canvas');
const ctx = canvas.getContext('2d');

const fileInput = document.getElementById('fileInput');
const uploadBtn = document.getElementById('uploadBtn');
const imageList = document.getElementById('imageList');
const imagesUl = document.getElementById('imagesUl');
const loadBtn = document.getElementById('loadBtn');
const saveBtn = document.getElementById('saveBtn');
const toleranceInput = document.getElementById('tolerance');

let currentImageName = null;
let currentImage = new Image();
let scale = 1;
let offsetX = 0;
let offsetY = 0;

let currentPolygon = [];
let polygons = [];

function setCanvasSize() {
	const wrap = canvas.parentElement;
	const rect = wrap.getBoundingClientRect();
	canvas.width = Math.floor(rect.width);
	canvas.height = Math.floor(rect.height);
	draw();
}

window.addEventListener('resize', setCanvasSize);
setCanvasSize();

function loadImage(name) {
	currentImageName = name;
	currentImage = new Image();
	currentImage.onload = () => {
		fitImage();
		loadAnnotations();
	};
	currentImage.src = `/api/image/${encodeURIComponent(name)}`;
}

function fitImage() {
	const cw = canvas.width;
	const ch = canvas.height;
	const iw = currentImage.naturalWidth;
	const ih = currentImage.naturalHeight;
	const s = Math.min(cw / iw, ch / ih);
	scale = s;
	offsetX = (cw - iw * s) / 2;
	offsetY = (ch - ih * s) / 2;
	draw();
}

function imgToCanvas(pt) {
	return [pt[0] * scale + offsetX, pt[1] * scale + offsetY];
}
function canvasToImg(x, y) {
	return [(x - offsetX) / scale, (y - offsetY) / scale];
}

function draw() {
	ctx.clearRect(0, 0, canvas.width, canvas.height);
	if (currentImage && currentImage.complete) {
		ctx.drawImage(currentImage, offsetX, offsetY, currentImage.naturalWidth * scale, currentImage.naturalHeight * scale);
	}

	// Draw existing polygons
	for (const poly of polygons) {
		drawPolygon(poly, 'rgba(16,185,129,0.25)', '#10b981');
	}
	// Draw current polygon
	if (currentPolygon.length > 0) {
		drawPolygon(currentPolygon, 'rgba(59,130,246,0.25)', '#3b82f6');
	}
}

function drawPolygon(poly, fillStyle, strokeStyle) {
	ctx.save();
	ctx.beginPath();
	for (let i = 0; i < poly.length; i++) {
		const [cx, cy] = imgToCanvas(poly[i]);
		if (i === 0) ctx.moveTo(cx, cy); else ctx.lineTo(cx, cy);
	}
	if (poly.length >= 3) ctx.closePath();
	ctx.fillStyle = fillStyle;
	ctx.strokeStyle = strokeStyle;
	ctx.lineWidth = 2;
	ctx.fill();
	ctx.stroke();
	// points
	ctx.fillStyle = strokeStyle;
	for (const p of poly) {
		const [cx, cy] = imgToCanvas(p);
		ctx.beginPath();
		ctx.arc(cx, cy, 3, 0, Math.PI * 2);
		ctx.fill();
	}
	ctx.restore();
}

canvas.addEventListener('click', async (e) => {
	if (!currentImageName) return;
	const rect = canvas.getBoundingClientRect();
	const x = e.clientX - rect.left;
	const y = e.clientY - rect.top;
	const [ix, iy] = canvasToImg(x, y);

	if (e.shiftKey) {
		// AI assist
		const tol = parseInt(toleranceInput.value || '15', 10);
		const res = await fetch('/api/ai/segment', {
			method: 'POST', headers: { 'Content-Type': 'application/json' },
			body: JSON.stringify({ image: currentImageName, x: Math.round(ix), y: Math.round(iy), tolerance: tol })
		});
		const data = await res.json();
		if (data && Array.isArray(data.points) && data.points.length >= 3) {
			currentPolygon = data.points;
			draw();
		}
		return;
	}

	// Manual point add
	currentPolygon.push([ix, iy]);
	draw();
});

window.addEventListener('keydown', (e) => {
	if (e.key === 'Backspace') {
		if (currentPolygon.length > 0) {
			currentPolygon.pop();
			draw();
		}
	}
	if (e.key === 'Enter') {
		if (currentPolygon.length >= 3) {
			polygons.push(currentPolygon);
			currentPolygon = [];
			draw();
		}
	}
});

async function refreshImageList() {
	const res = await fetch('/api/images');
	const data = await res.json();
	imageList.innerHTML = '';
	imagesUl.innerHTML = '';
	for (const name of data.images || []) {
		const opt = document.createElement('option');
		opt.value = name; opt.textContent = name; imageList.appendChild(opt);
		const li = document.createElement('li');
		li.textContent = name; li.addEventListener('click', () => loadImage(name));
		imagesUl.appendChild(li);
	}
}

uploadBtn.addEventListener('click', async () => {
	const file = fileInput.files && fileInput.files[0];
	if (!file) return;
	const form = new FormData();
	form.append('file', file);
	await fetch('/api/upload', { method: 'POST', body: form });
	await refreshImageList();
});

loadBtn.addEventListener('click', () => {
	const name = imageList.value;
	if (name) loadImage(name);
});

saveBtn.addEventListener('click', async () => {
	if (!currentImageName) return;
	const payload = {
		version: '5.0.0',
		imagePath: currentImageName,
		imageData: null,
		shapes: polygons.map((poly, idx) => ({
			label: `object_${idx + 1}`,
			points: poly,
			shape_type: 'polygon'
		}))
	};
	const base = currentImageName.replace(/\.[^.]+$/, '');
	await fetch(`/api/annotations/${encodeURIComponent(base)}.json`, {
		method: 'POST', headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify(payload)
	});
	alert('Saved');
});

async function loadAnnotations() {
	polygons = [];
	currentPolygon = [];
	const base = currentImageName.replace(/\.[^.]+$/, '');
	const res = await fetch(`/api/annotations/${encodeURIComponent(base)}.json`);
	if (res.ok) {
		const data = await res.json();
		if (data && Array.isArray(data.shapes)) {
			for (const s of data.shapes) {
				if (s.shape_type === 'polygon' && Array.isArray(s.points)) {
					const pts = s.points.map(p => [p[0], p[1]]);
					polygons.push(pts);
				}
			}
		}
	}
	draw();
}

refreshImageList();