import { ProofChainDataProvider } from "./data-provider";
import { GatewayDataProvider } from "./gateway-provider";

const gatewayProvider = new GatewayDataProvider();

export function getDataProvider(): ProofChainDataProvider {
  return gatewayProvider;
}
