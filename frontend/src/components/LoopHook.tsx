import React, {useEffect, useRef } from 'react';

export const LoopHook = (callback: any) => {
    const animationRef: any = useRef(); // To store the animation frame id
	const lastTime: any = useRef();

    const loop_hook = (time: number) => {
		if (lastTime.current != undefined) {
			const delta : number = time - lastTime.current
            callback(delta)
		}
		lastTime.current = time
		animationRef.current = requestAnimationFrame(loop_hook);

	};

	useEffect(() => {
		animationRef.current = requestAnimationFrame(loop_hook);
		return () => {
			if (animationRef.current)
				cancelAnimationFrame(animationRef.current);
		};
	}, []);
}
 
