import React from 'react';
import { AGENT_CONFIG } from './agentConfig';
import styles from './AgentAttribution.module.css';

interface Props {
  agentId: string;
  size?: 'small' | 'medium' | 'large';
  variant?: 'inline' | 'badge' | 'chip';
  showPackIcon?: boolean;
  className?: string;
  onClick?: (agentId: string) => void;
}

export const AgentAttribution: React.FC<Props> = ({
  agentId,
  size = 'medium',
  variant = 'badge',
  showPackIcon = true,
  className = '',
  onClick,
}) => {
  const config = AGENT_CONFIG[agentId];
  
  if (!config) return null;

  const sizeClass = styles[`size${size.charAt(0).toUpperCase() + size.slice(1)}`];
  const variantClass = styles[`variant${variant.charAt(0).toUpperCase() + variant.slice(1)}`];

  const handleClick = () => {
    onClick?.(agentId);
  };

  return (
    <span
      className={`${styles.agentTag} ${sizeClass} ${variantClass} ${className}`}
      style={{
        backgroundColor: config.bgColor,
        color: config.color,
        borderColor: config.color,
      }}
      onClick={handleClick}
      title={`${config.name} (${config.packName}) - ${config.description}`}
    >
      {showPackIcon && (
        <span className={styles.agentIcon}>{config.icon}</span>
      )}
      <span className={styles.agentName}>
        {variant === 'inline' ? config.name : config.packName}
      </span>
      {variant === 'badge' && (
        <span className={styles.agentPack}>{config.packName}</span>
      )}
    </span>
  );
};
