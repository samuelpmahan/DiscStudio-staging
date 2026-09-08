from pyto import Calculation, Part, PCR, PxC

value = Part("px.value")
double = Calculation("fn.double", lambda args: args["value"] * 2)
pxc = PxC()
pxc.set(value, 21)
pcr = PCR("demo")
pcr.calc("main", double, id="double", value=value)
print(pcr.run(pxc).results["double"])
