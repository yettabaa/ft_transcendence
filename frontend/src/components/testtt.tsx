const ballElem: any = useRef();
    const tableElem: any = useRef();
    const controlledPaddleElem: any = useRef();
    const paddleBootElem: any = useRef();

    // const ball: any = useRef();
    // const paddleBoot: any = useRef();
    // const controlledPaddle: any = useRef();
    const game: any = useRef();
    const posPaddle = useRef(0);

    const [ballSize, setBallSize] = useState<number>(0);
    const handleResize = () => {
        if (tableElem.current) {
            const tableWidth = tableElem.current.offsetWidth;
            console.log(tableWidth)
            const radius = tableWidth * 0.03; // 3% of table width
            setBallSize(radius);
        }
    }
    const handelMouse = (e: any) => {
        const tableDimention = tableElem.current.getBoundingClientRect();
        posPaddle.current = ((e.y - tableDimention.top)
        / tableDimention.height) * 100;
        (posPaddle.current < 0) && (posPaddle.current = 0);
        (posPaddle.current > 100) && (posPaddle.current = 100);
        game.current.rightPaddle.y = posPaddle.current;
    }
    useEffect(() => {
        if (ballElem.current && tableElem.current &&
            controlledPaddleElem.current && paddleBootElem.current) {
            // ball.current = new Ball(ballElem.current, tableElem.current);
            // paddleBoot.current = new Paddle(paddleBootElem.current, tableElem.current);
            // controlledPaddle.current = new Paddle(controlledPaddleElem.current, tableElem.current);
            game.current = new Game(ballElem.current, controlledPaddleElem.current, paddleBootElem.current)
            
            handleResize()
            document.addEventListener("mousemove", handelMouse);
            document.addEventListener('resize', handleResize);
            return () => {
                document.removeEventListener("mousemove", handelMouse);
                document.removeEventListener('resize', handleResize);
            }
        }
    }, [])
    
    LoopHook((delta: number) => {
        if (ballElem.current && tableElem.current &&
            controlledPaddleElem.current && paddleBootElem.current) {
                // ball.current.update(delta, controlledPaddle.current, paddleBoot.current);
                // paddleBoot.current.update(delta, ball.current.y);
                // if (ball.current.isFailure()) {
                    //     ball.current.reset();
                    // }
            game.current.game(delta,10, 300)

        }
    });