import BallComp from "./BallComp.tsx"

const Index = () => {
	return (
		<div className="bg-[#0C0D0F] w-full h-[100vh] px-10 flex justify-center items-center">
			<div className="flex flex-col h-[58vh] w-[63vw]">
				<div className="h-[10%] flex flex-row justify-center items-center">
					<div className="p-[0.5rem] border-r">0</div>
					<div className="p-[0.5rem] ">0</div>
				</div>
				<BallComp />
			</div>
		</div>
	);
}

export default Index;
