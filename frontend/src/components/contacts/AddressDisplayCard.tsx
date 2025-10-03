import React from "react";
import { MapPin, Navigation, ExternalLink } from "lucide-react";
import Card from "../ui/Card";

interface AddressData {
  id?: string | number;
  street: string;
  number?: string;
  complement?: string;
  details?: string;
  neighborhood: string;
  city: string;
  state: string;
  postal_code?: string;
  zip_code?: string;
  country?: string;
  type: string;
  is_principal?: boolean;
  description?: string;
}

interface AddressDisplayCardProps {
  addresses: AddressData[];
  title?: string;
  getAddressTypeLabel?: (type: string) => string;
  formatZipCode?: (zipCode: string) => string;
  onOpenGoogleMaps?: (address: AddressData) => void;
  onOpenWaze?: (address: AddressData) => void;
}

const AddressDisplayCard: React.FC<AddressDisplayCardProps> = ({
  addresses,
  title = "Endereços",
  getAddressTypeLabel = (type) => type,
  formatZipCode = (zipCode) => {
    if (!zipCode) return "";
    const clean = zipCode.replace(/\D/g, "");
    if (clean.length === 8) {
      return clean.replace(/(\d{5})(\d{3})/, "$1-$2");
    }
    return zipCode;
  },
  onOpenGoogleMaps = (address) => {
    const zipCode = address.postal_code || address.zip_code || "";
    const query = encodeURIComponent(
      `${address.street}, ${address.number || ""}, ${address.city}, ${
        address.state
      }, ${zipCode}, ${address.country || "Brasil"}`
    );
    const url = `https://www.google.com/maps/search/?api=1&query=${query}`;
    window.open(url, "_blank");
  },
  onOpenWaze = (address) => {
    const query = encodeURIComponent(
      `${address.street}, ${address.number || ""}, ${address.city}, ${
        address.state
      }`
    );
    const url = `https://waze.com/ul?q=${query}`;
    window.open(url, "_blank");
  },
}) => {
  return (
    <Card title={title}>
      {!addresses || addresses.length === 0 ? (
        <p className="text-sm text-muted-foreground">
          Nenhum endereço cadastrado
        </p>
      ) : (
      <div className="space-y-4">
        {addresses.map((address, index) => (
          <div key={address.id || index} className="p-4 bg-muted/30 rounded-lg">
            <div className="flex items-start gap-3">
              <div className="p-2 bg-purple-100 dark:bg-purple-900 rounded-lg">
                <MapPin className="h-4 w-4 text-purple-600 dark:text-purple-300" />
              </div>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="font-medium text-foreground">
                    {getAddressTypeLabel(address.type)}
                  </span>
                  {address.is_principal && (
                    <span className="px-2 py-0.5 bg-primary/10 text-primary text-xs rounded">
                      Principal
                    </span>
                  )}
                </div>

                <p className="font-medium text-foreground">
                  {address.street}
                  {address.number && `, ${address.number}`}
                  {(address.complement || address.details) &&
                    ` - ${address.complement || address.details}`}
                </p>

                <p className="text-sm text-muted-foreground">
                  {address.neighborhood} - {address.city}/{address.state}
                </p>

                <p className="text-sm text-muted-foreground">
                  CEP:{" "}
                  {formatZipCode(address.postal_code || address.zip_code || "")}
                  {address.country &&
                    address.country !== "Brasil" &&
                    ` - ${address.country}`}
                </p>

                {address.description && (
                  <p className="text-sm text-muted-foreground mt-1">
                    {address.description}
                  </p>
                )}

                {/* Action Buttons */}
                <div className="flex gap-2 mt-2">
                  <button
                    onClick={() => onOpenGoogleMaps(address)}
                    className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-blue-50 text-blue-600 rounded hover:bg-blue-100 transition-colors"
                  >
                    <ExternalLink className="h-3 w-3" />
                    Google Maps
                  </button>
                  <button
                    onClick={() => onOpenWaze(address)}
                    className="inline-flex items-center gap-1 px-2 py-1 text-xs bg-purple-50 text-purple-600 rounded hover:bg-purple-100 transition-colors"
                  >
                    <Navigation className="h-3 w-3" />
                    Waze
                  </button>
                </div>

                {/* Full-width buttons for company style (optional) */}
                <div className="mt-3 hidden">
                  <div className="grid grid-cols-2 gap-2">
                    <button
                      onClick={() => onOpenGoogleMaps(address)}
                      className="flex items-center justify-center gap-2 p-3 bg-red-100 hover:bg-red-200 dark:bg-red-900/30 dark:hover:bg-red-900/50 text-red-700 dark:text-red-300 rounded-lg transition-colors"
                    >
                      <Navigation className="h-5 w-5" />
                      <span className="text-sm font-medium">Maps</span>
                    </button>
                    <button
                      onClick={() => onOpenWaze(address)}
                      className="flex items-center justify-center gap-2 p-3 bg-purple-100 hover:bg-purple-200 dark:bg-purple-900/30 dark:hover:bg-purple-900/50 text-purple-700 dark:text-purple-300 rounded-lg transition-colors"
                    >
                      <ExternalLink className="h-5 w-5" />
                      <span className="text-sm font-medium">Waze</span>
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>
        ))}
      </div>
      )}
    </Card>
  );
};

export default AddressDisplayCard;
