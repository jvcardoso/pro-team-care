/**
 * Logger centralizado para toda a aplicação
 * 🎯 Elimina duplicação de console.log espalhados e padroniza logging
 */

const LOG_LEVELS = {
  ERROR: 0,
  WARN: 1,
  INFO: 2,
  DEBUG: 3,
  TRACE: 4,
};

class Logger {
  constructor() {
    this.level = this.getLogLevel();
    this.context = "App";
  }

  getLogLevel() {
    // Detectar ambiente de desenvolvimento
    let isDev = false;

    try {
      // Tentar acessar import.meta.env (Vite)
      isDev = import.meta.env?.DEV === true;
    } catch (e) {
      // Fallback: verificar hostname ou outras condições
      isDev =
        window.location.hostname === "localhost" ||
        window.location.hostname === "127.0.0.1" ||
        window.location.port === "3000" ||
        window.location.port === "3001";
    }

    const envLevel = isDev ? "DEBUG" : "INFO";
    return LOG_LEVELS[envLevel] || LOG_LEVELS.INFO;
  }

  setContext(context) {
    this.context = context;
    return this;
  }

  createLogger(context) {
    const logger = new Logger();
    logger.context = context;
    return logger;
  }

  formatMessage(level, message, data) {
    const timestamp = new Date().toISOString();
    const contextStr = this.context ? `[${this.context}]` : "";
    const prefix = `${timestamp} ${level} ${contextStr}`;

    if (data) {
      return [prefix, message, data];
    }
    return [prefix, message];
  }

  error(message, data) {
    if (this.level >= LOG_LEVELS.ERROR) {
      console.error(...this.formatMessage("ERROR", message, data));
    }
  }

  warn(message, data) {
    if (this.level >= LOG_LEVELS.WARN) {
      console.warn(...this.formatMessage("WARN", message, data));
    }
  }

  info(message, data) {
    if (this.level >= LOG_LEVELS.INFO) {
      console.log(...this.formatMessage("INFO", message, data));
    }
  }

  debug(message, data) {
    if (this.level >= LOG_LEVELS.DEBUG) {
      console.log(...this.formatMessage("DEBUG", message, data));
    }
  }

  trace(message, data) {
    if (this.level >= LOG_LEVELS.TRACE) {
      console.log(...this.formatMessage("TRACE", message, data));
    }
  }

  // Métodos especializados para diferentes contextos
  api(action, details) {
    this.info(`🔗 API ${action}`, details);
  }

  service(action, details) {
    this.info(`⚙️ Service ${action}`, details);
  }

  component(action, details) {
    this.debug(`🧩 Component ${action}`, details);
  }

  performance(action, duration, details) {
    this.info(`⏱️ Performance ${action}`, { duration, ...details });
  }

  validation(field, result, details) {
    if (result.isValid) {
      this.debug(`✅ Validation ${field} passed`, details);
    } else {
      this.warn(`❌ Validation ${field} failed`, {
        message: result.message,
        ...details,
      });
    }
  }

  enrichment(source, action, details) {
    this.info(`🔍 ${source} ${action}`, details);
  }

  cache(action, key, details) {
    this.debug(`💾 Cache ${action} for ${key}`, details);
  }
}

// Instância singleton
const logger = new Logger();

// Loggers especializados
export const apiLogger = logger.createLogger("API");
export const serviceLogger = logger.createLogger("Service");
export const componentLogger = logger.createLogger("Component");
export const validationLogger = logger.createLogger("Validation");

export default logger;
