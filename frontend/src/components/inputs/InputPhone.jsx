import React from "react";
import BaseInputField from "./BaseInputField";
import { phoneConfig } from "../../utils/inputHelpers.tsx";
import { removeNonNumeric } from "../../utils/validators";

const InputPhone = ({
  label = "Telefone",
  countryCode = "55",
  onChange,
  value,
  ...props
}) => {
  const handleChange = (event) => {
    if (onChange) {
      onChange(event);
    }
  };

  const getPhoneType = (phoneNumber) => {
    const numbers = removeNonNumeric(phoneNumber || "");
    if (numbers.length === 11) {
      return "Celular";
    } else if (numbers.length === 10) {
      return "Fixo";
    }
    return "";
  };

  const phoneType = getPhoneType(value);
  const customLabel = phoneType ? (
    <div className="flex items-center justify-between w-full">
      <span>{label}</span>
      <span className="text-xs text-muted-foreground">{phoneType}</span>
    </div>
  ) : (
    label
  );

  const customHelper = value ? (
    <span className="text-xs text-muted-foreground">
      {phoneType && `${phoneType} • `}+{countryCode} {removeNonNumeric(value)}
    </span>
  ) : undefined;

  return (
    <BaseInputField
      label={customLabel}
      value={value}
      onChange={handleChange}
      formatterConfig={phoneConfig.formatter}
      validatorConfig={phoneConfig.validator}
      leftIcon={phoneConfig.icon}
      placeholder={phoneConfig.placeholder}
      type="tel"
      inputMode={phoneConfig.inputMode}
      autoComplete={phoneConfig.autoComplete}
      successMessage={phoneConfig.successMessage}
      progressMessage={phoneConfig.progressMessage}
      helper={customHelper}
      showProgressIndicator
      {...props}
    />
  );
};

export default InputPhone;
